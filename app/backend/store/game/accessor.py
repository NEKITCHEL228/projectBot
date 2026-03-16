from typing import TYPE_CHECKING
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.backend.base.base_accessor import BaseAccessor
from app.backend.game.models import (
    GameModel,
    GameUserModel,
    GameStatusEnum,
    CompanySharesModel,
    UserCompanyShareModel,
    UserBalanceModel,
)
from app.backend.store.tg_api.game_builders import get_initial_companies, build_round_start_message, get_random_events, build_game_over_message, MAIN_MENU_BUTTONS
from app.backend.user.models import UserModel

if TYPE_CHECKING:
    from app.backend.web.app import Application


class GameAccessor(BaseAccessor):
    def __init__(self, app: "Application"):
        self.app = app

    # ── Активная игра ─────────────────────────────────────────────────────────

    async def get_active_game(self, chat_id: int) -> GameModel | None:
        query = (
            select(GameModel)
            .where(
                GameModel.chat_id == chat_id,
                GameModel.game_status.in_([
                    GameStatusEnum.WAITING_FOR_PLAYERS,
                    GameStatusEnum.IN_PROGRESS,
                ]),
            )
            .options(
                selectinload(GameModel.game_user).selectinload(GameUserModel.user)
            )
        )
        async with self.app.database.session() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

    # ── Создание / управление игрой ───────────────────────────────────────────
        
    async def create_game(self, chat_id: int) -> GameModel:
        game = GameModel(
            chat_id=chat_id,
            game_status=GameStatusEnum.WAITING_FOR_PLAYERS,
            max_rounds=10,
        )
        async with self.app.database.session() as session:
            session.add(game)
            await session.commit()
            await session.refresh(game)
        return game

    async def start_game(self, game_id: int) -> None:
        query = select(GameModel).where(GameModel.game_id == game_id)
        async with self.app.database.session() as session:
            result = await session.execute(query)
            game = result.scalar_one_or_none()
            if game:
                game.game_status = GameStatusEnum.IN_PROGRESS
                game.game_trading_session_round = 1
                
                for company in get_initial_companies():
                    session.add(CompanySharesModel(
                        game_id=game_id,
                        company_share_name=company["name"],
                        company_share_price=company["price"],
                    ))
                
                await session.commit()

    async def finish_game(self, game_id: int) -> None:
        query = select(GameModel).where(GameModel.game_id == game_id)
        async with self.app.database.session() as session:
            result = await session.execute(query)
            game = result.scalar_one_or_none()
            
            if not game:
                return
            
            round_num = game.game_trading_session_round
            
            players_q = (
                select(GameUserModel)
                .where(GameUserModel.game_id == game_id)
                .options(selectinload(GameUserModel.user), selectinload(GameUserModel.balance))
                )
            
            players_result = await session.execute(players_q)
            game_users = players_result.scalars().all()
            
            players_balances = [
            {
                "name": gu.user.name,
                "balance": float(gu.balance.full_balance) if gu.balance else 0.0,
            }
            for gu in game_users
            ]
            
            # Определяем победителя
            winner = max(game_users, key=lambda gu: float(gu.balance.full_balance) if gu.balance else 0.0, default=None)

            # Обновляем статистику всех игроков
            for gu in game_users:
                gu.user.games_played += 1
                if winner and gu.game_user_id == winner.game_user_id:
                    gu.user.games_won += 1
                # Обновляем max_balance если текущий баланс выше
                balance = float(gu.balance.full_balance) if gu.balance else 0.0
                if balance > float(gu.user.max_balance):
                    gu.user.max_balance = balance
                
                game.game_status = GameStatusEnum.FINISHED
                await session.commit()
            
        chat_id = game.chat_id
        text = build_game_over_message(round_num, players_balances)
        await self.app.store.tg_api.send_keyboard(chat_id, text, MAIN_MENU_BUTTONS)

    # ── Игроки ────────────────────────────────────────────────────────────────

    async def add_player_to_game(self, game_id: int, user_id: int) -> bool:
        check = select(GameUserModel).where(
            GameUserModel.game_id == game_id,
            GameUserModel.user_id == user_id,
        )
        async with self.app.database.session() as session:
            result = await session.execute(check)
            if result.scalar_one_or_none():
                return False
            game_user = GameUserModel(game_id=game_id, user_id=user_id)
            session.add(game_user)
            await session.flush()  # получаем game_user_id до commit
            session.add(UserBalanceModel(game_user_id=game_user.game_user_id))
            await session.commit()
        return True

    async def remove_player_from_game(self, game_id: int, user_id: int) -> bool:
        query = delete(GameUserModel).where(
            GameUserModel.game_id == game_id,
            GameUserModel.user_id == user_id,
        )
        async with self.app.database.session() as session:
            result = await session.execute(query)
            await session.commit()
            return result.rowcount > 0

    async def get_players(self, game_id: int):
        query = (
            select(GameUserModel)
            .where(GameUserModel.game_id == game_id)
            .options(selectinload(GameUserModel.user))
        )
        async with self.app.database.session() as session:
            result = await session.execute(query)
            return [gu.user for gu in result.scalars().all()]

    # ── Вспомогательный метод: получить GameUserModel с балансом ─────────────

    async def _get_game_user_with_balance(
        self, session, game_id: int, user_id: int
    ) -> GameUserModel | None:
        query = (
            select(GameUserModel)
            .where(
                GameUserModel.game_id == game_id,
                GameUserModel.user_id == user_id,
            )
            .options(selectinload(GameUserModel.balance))
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
    
    # ── Вспомогательный метод: Пересчитывает company_share_balance и full_balance для всех игроков ─────────────
    
    async def _recalculate_balances(self, session, game_id: int) -> None:
        # Загружаем актуальные цены
        companies_result = await session.execute(
            select(CompanySharesModel).where(CompanySharesModel.game_id == game_id)
        )
        price_map = {
            c.company_share_id: float(c.company_share_price)
            for c in companies_result.scalars().all()
        }

        # Загружаем всех игроков с балансами и акциями
        players_q = (
            select(GameUserModel)
            .where(GameUserModel.game_id == game_id)
            .options(
                selectinload(GameUserModel.balance),
                selectinload(GameUserModel.company_shares).selectinload(
                    UserCompanyShareModel.company_share
                ),
            )
        )
        result = await session.execute(players_q)
        game_users = result.scalars().all()

        for gu in game_users:
            if not gu.balance:
                continue

            # Считаем стоимость всех акций игрока по новым ценам
            shares_value = sum(
                s.company_share_count * price_map.get(s.company_share_id, 0.0)
                for s in gu.company_shares
            )

            gu.balance.company_share_balance = shares_value
            gu.balance.full_balance = float(gu.balance.pure_balance) + shares_value
                    
    # ── Вспомогательный метод: Вывод сообщения о раунде ─────────────
    
    async def print_round_message(self, game_id: int, events: list[dict] | None = None) -> None:
        """
        Выводит информацию о текущем раунде.
        events=None означает первый раунд — цены показываются без изменений.
        """
        async with self.app.database.session() as session:
            game_q = select(GameModel).where(GameModel.game_id == game_id)
            result = await session.execute(game_q)
            game = result.scalar_one_or_none()
            if not game:
                return

            players_q = (
                select(GameUserModel)
                .where(GameUserModel.game_id == game_id)
                .options(
                    selectinload(GameUserModel.user),
                    selectinload(GameUserModel.balance),
                )
            )
            result = await session.execute(players_q)
            game_users = result.scalars().all()

            players_balances = [
                {
                    "name": gu.user.name,
                    "balance": float(gu.balance.full_balance) if gu.balance else 0.0,
                }
                for gu in game_users
            ]

            companies_result = await session.execute(
                select(CompanySharesModel).where(CompanySharesModel.game_id == game_id)
            )
            companies_data = [
                {"name": c.company_share_name, "price": float(c.company_share_price)}
                for c in companies_result.scalars().all()
            ]

        # Если события не переданы — первый раунд, цены без изменений
        round_events = events if events is not None else [
            {
                "name": c["name"],
                "old_price": c["price"],
                "new_price": c["price"],
                "direction": "none",
                "percent": 0,
            }
            for c in companies_data
        ]

        text = build_round_start_message(game.game_trading_session_round, players_balances, round_events)
        await self.app.store.tg_api.send_message(game.chat_id, text)

    # ── Акции / компании ──────────────────────────────────────────────────────

    async def get_companies(self, game_id: int) -> list[dict]:
        """Список компаний игры: [{"name": str, "price": float}, ...]"""
        query = select(CompanySharesModel).where(CompanySharesModel.game_id == game_id)
        async with self.app.database.session() as session:
            result = await session.execute(query)
            companies = result.scalars().all()
        return [
            {"name": c.company_share_name, "price": float(c.company_share_price)}
            for c in companies
        ]

    async def buy_shares(
        self, game_id: int, user_id: int, company_name: str, quantity: int
    ) -> tuple[bool, str]:
        """Покупает акции. Возвращает (success, message)."""
        async with self.app.database.session() as session:
            # Найти компанию
            company_q = select(CompanySharesModel).where(
                CompanySharesModel.game_id == game_id,
                CompanySharesModel.company_share_name == company_name,
            )
            result = await session.execute(company_q)
            company = result.scalar_one_or_none()

            if not company:
                return False, f"❌ Компания «{company_name}» не найдена."

            total_cost = float(company.company_share_price) * quantity

            # Получить GameUserModel + баланс
            game_user = await self._get_game_user_with_balance(session, game_id, user_id)
            if not game_user:
                return False, "❌ Вы не участвуете в этой игре."

            balance = game_user.balance
            if not balance or float(balance.pure_balance) < total_cost:
                current = float(balance.pure_balance) if balance else 0.0
                return False, (
                    f"❌ Недостаточно средств.\n"
                    f"Нужно: {total_cost:.2f} ₽ · Баланс: {current:.2f} ₽"
                )

            # Списать с баланса
            balance.pure_balance = float(balance.pure_balance) - total_cost
            balance.company_share_balance = (
                float(balance.company_share_balance) + total_cost
            )

            # Добавить / обновить позицию в портфеле
            share_q = select(UserCompanyShareModel).where(
                UserCompanyShareModel.game_user_id == game_user.game_user_id,
                UserCompanyShareModel.company_share_id == company.company_share_id,
            )
            result = await session.execute(share_q)
            share = result.scalar_one_or_none()

            if share:
                share.company_share_count += quantity
            else:
                session.add(UserCompanyShareModel(
                    game_user_id=game_user.game_user_id,
                    company_share_id=company.company_share_id,
                    company_share_count=quantity,
                ))

            await session.commit()

        return True, (
            f"✅ Куплено {quantity} шт. «{company_name}» "
            f"по {float(company.company_share_price):.2f} ₽.\n"
            f"Списано: {total_cost:.2f} ₽"
        )

    async def sell_shares(
        self, game_id: int, user_id: int, company_name: str, quantity: int
    ) -> tuple[bool, str]:
        """Продаёт акции. Возвращает (success, message)."""
        async with self.app.database.session() as session:
            # Найти компанию
            company_q = select(CompanySharesModel).where(
                CompanySharesModel.game_id == game_id,
                CompanySharesModel.company_share_name == company_name,
            )
            result = await session.execute(company_q)
            company = result.scalar_one_or_none()

            if not company:
                return False, f"❌ Компания «{company_name}» не найдена."

            # Получить GameUserModel + баланс
            game_user = await self._get_game_user_with_balance(session, game_id, user_id)
            if not game_user:
                return False, "❌ Вы не участвуете в этой игре."

            # Проверить позицию в портфеле
            share_q = select(UserCompanyShareModel).where(
                UserCompanyShareModel.game_user_id == game_user.game_user_id,
                UserCompanyShareModel.company_share_id == company.company_share_id,
            )
            result = await session.execute(share_q)
            share = result.scalar_one_or_none()

            held = share.company_share_count if share else 0
            if not share or held < quantity:
                return False, (
                    f"❌ Недостаточно акций «{company_name}».\n"
                    f"В портфеле: {held} шт., запрошено: {quantity} шт."
                )

            total_revenue = float(company.company_share_price) * quantity

            # Обновить портфель
            share.company_share_count -= quantity
            if share.company_share_count == 0:
                await session.delete(share)

            # Вернуть деньги на баланс
            balance = game_user.balance
            if balance:
                balance.pure_balance = float(balance.pure_balance) + total_revenue
                balance.company_share_balance = max(
                    0.0, float(balance.company_share_balance) - total_revenue
                )

            await session.commit()

        return True, (
            f"✅ Продано {quantity} шт. «{company_name}» "
            f"по {float(company.company_share_price):.2f} ₽.\n"
            f"Получено: {total_revenue:.2f} ₽"
        )

    async def get_portfolio(
        self, game_id: int, user_id: int
    ) -> tuple[list[dict], float]:
        """Возвращает (портфель, pure_balance)."""
        async with self.app.database.session() as session:
            game_user = await self._get_game_user_with_balance(session, game_id, user_id)
            if not game_user:
                return [], 0.0

            shares_q = (
                select(UserCompanyShareModel)
                .where(UserCompanyShareModel.game_user_id == game_user.game_user_id)
                .options(selectinload(UserCompanyShareModel.company_share))
            )
            result = await session.execute(shares_q)
            shares = result.scalars().all()

            balance = float(game_user.balance.pure_balance) if game_user.balance else 0.0

        portfolio = [
            {
                "name": s.company_share.company_share_name,
                "quantity": s.company_share_count,
                "price": float(s.company_share.company_share_price),
            }
            for s in shares
        ]
        return portfolio, balance

    # ── Раунды ────────────────────────────────────────────────────────────────

    async def finish_round(self, chat_id: int, game_id: int) -> None:
        manager = self.app.store.bots_manager
        manager.reset_turns(chat_id)

        new_round = 1

        # Увеличиваем раунд
        async with self.app.database.session() as session:
            result = await session.execute(
                select(GameModel).where(GameModel.game_id == game_id)
            )
            game = result.scalar_one_or_none()
            if game:
                new_round = game.game_trading_session_round + 1
                if new_round > game.max_rounds:
                    await self.finish_game(game_id)
                    return
                game.game_trading_session_round = new_round
                await session.commit()

        # Читаем старые цены, генерируем события, применяем новые цены
        async with self.app.database.session() as session:
            companies_result = await session.execute(
                select(CompanySharesModel).where(CompanySharesModel.game_id == game_id)
            )
            companies_rows = companies_result.scalars().all()
            companies_data = [
                {"name": c.company_share_name, "price": float(c.company_share_price)}
                for c in companies_rows
            ]

            # События
            events = get_random_events(companies_data)

            # Применяем новые цены в БД
            price_map = {e["name"]: e["new_price"] for e in events}
            for company_row in companies_rows:
                if company_row.company_share_name in price_map:
                    company_row.company_share_price = price_map[company_row.company_share_name]

            await session.commit()

            # Пересчитываем балансы по новым ценам
            await self._recalculate_balances(session, game_id)
            await session.commit()

            # Читаем балансы ПОСЛЕ пересчёта
            players_q = (
                select(GameUserModel)
                .where(GameUserModel.game_id == game_id)
                .options(
                    selectinload(GameUserModel.user),
                    selectinload(GameUserModel.balance),
                )
            )
            result = await session.execute(players_q)
            game_users = result.scalars().all()

            players_balances = [
                {
                    "name": gu.user.name,
                    "balance": float(gu.balance.full_balance) if gu.balance else 0.0,
                }
                for gu in game_users
            ]

        text = build_round_start_message(new_round, players_balances, events)
        await self.app.store.tg_api.send_message(chat_id, text)