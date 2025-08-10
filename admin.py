# admin.py
from sqladmin import Admin, ModelView
from models import User, PostbackLog
from database import engine

# --- Админ-представления ---

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

    # пароль не показываем/не редактируем из формы
    column_details_exclude_list = [User.password,]
    form_excluded_columns = [User.password, User.created_at, User.updated_at]

class PostbackAdmin(ModelView, model=PostbackLog):
    name = "Postback"
    name_plural = "Postbacks"

    column_list = [
        PostbackLog.id, PostbackLog.event, PostbackLog.click_id, PostbackLog.trader_id,
        PostbackLog.amount, PostbackLog.currency, PostbackLog.processed,
        PostbackLog.created_at, PostbackLog.processed_at
    ]
    column_searchable_list = [PostbackLog.event, PostbackLog.click_id, PostbackLog.trader_id]
    column_sortable_list = [PostbackLog.id, PostbackLog.created_at, PostbackLog.amount]

def init_admin(app):
    # base_url="/admin" — админка доступна по /admin, её статика — /admin/static (не конфликтует с /static)
    admin = Admin(app, engine, base_url="/admin")
    admin.add_view(UserAdmin)
    admin.add_view(PostbackAdmin)
