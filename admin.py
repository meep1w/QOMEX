# admin.py
from sqladmin import Admin, ModelView, action
from wtforms import PasswordField
from models import User, PostbackLog
from database import engine, SessionLocal
from auth import hash_password, ensure_unique_click_id, attach_pending_postbacks  # используем твои функции

class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"

    column_list = [
        User.id, User.login, User.email, User.trader_id,
        User.first_deposit, User.total_deposit, User.deposit_verified,
        User.created_at, User.updated_at
    ]
    column_searchable_list = [User.login, User.email, User.trader_id]
    column_sortable_list = [User.id, User.created_at, User.total_deposit]

    # пароль не показываем как колонку/поле
    column_details_exclude_list = [User.password]
    form_excluded_columns = [User.password, User.created_at, User.updated_at]

    # добавляем поле для ввода нового пароля
    form_extra_fields = {
        "new_password": PasswordField("New password")
    }

    # опционально запретить удаление (чтобы случайно не унесли юзера с логами)
    # can_delete = False

    def on_model_change(self, form, model, is_created):
        # захэшовать пароль, если ввели
        pwd = form.data.get("new_password")
        if pwd:
            model.password = hash_password(pwd)

        # выдать click_id если пусто (для новых)
        if is_created and not model.click_id:
            with SessionLocal() as db:
                model.click_id = ensure_unique_click_id(db, None)

class PostbackAdmin(ModelView, model=PostbackLog):
    name = "Postback"
    name_plural = "Postbacks"

    column_list = [
        PostbackLog.id, PostbackLog.event, PostbackLog.click_id, PostbackLog.trader_id,
        PostbackLog.amount, PostbackLog.currency, PostbackLog.processed,
        PostbackLog.created_at, PostbackLog.processed_at, PostbackLog.user_id
    ]
    column_searchable_list = [PostbackLog.event, PostbackLog.click_id, PostbackLog.trader_id]
    column_sortable_list = [PostbackLog.id, PostbackLog.created_at, PostbackLog.amount]

    # Удобная кнопка: «привязать и обработать» выбранные логи
    @action(
        name="process_logs",
        label="Attach & process",
        confirmation_message="Привязать выбранные логи к пользователям и обновить депозиты?"
    )
    def process_logs(self, ids):
        with SessionLocal() as db:
            logs = db.query(PostbackLog).filter(PostbackLog.id.in_(ids)).all()
            affected = set()
            for pb in logs:
                # находим юзера по click_id или trader_id
                user = None
                if pb.click_id:
                    user = db.query(User).filter(User.click_id == pb.click_id).first()
                if not user and pb.trader_id:
                    user = db.query(User).filter(User.trader_id == pb.trader_id).first()
                if user:
                    # твоя функция подтягивает все pending-постбэки и обновляет суммы
                    attach_pending_postbacks(db, user)
                    affected.add(user.id)
            return f"Processed for users: {len(affected)}"

def init_admin(app):
    admin = Admin(app, engine, base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(PostbackAdmin)
