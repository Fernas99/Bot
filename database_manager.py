import sqlite3
from models import User, Channel

DATABASE = 'database.db'

class DatabaseManager:
    def __init__(self, database=DATABASE):
        self.database = database

    def get_db_connection(self):
        conn = sqlite3.connect(self.database)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with app.app_context():
            db.create_all()
        print("Database initialized.")

    def add_user(self, username, password):
        with app.app_context():
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
        print(f"User {username} added successfully.")

    def list_users(self):
        conn = self.get_db_connection()
        users = conn.execute('SELECT * FROM user').fetchall()
        conn.close()
        for user in users:
            print(f"User ID: {user['id']}, Username: {user['username']}")

    def list_channels(self):
        conn = self.get_db_connection()
        channels = conn.execute('SELECT * FROM channel').fetchall()
        conn.close()
        for channel in channels:
            print(f"Channel ID: {channel['id']}, Channel Name: {channel['channel_id']}, "
                  f"Button Name: {channel['button_name']}, "
                  f"Subscription Link: {channel['subscription_link']}, "
                  f"Owner ID: {channel['user_id']}")

    def delete_user(self, username):
        with app.app_context():
            user = User.query.filter_by(username=username).first()
            if user:
                db.session.delete(user)
                db.session.commit()
                print(f"User {username} deleted successfully.")
            else:
                print(f"User {username} not found.")

    def delete_channel(self, channel_id):
        with app.app_context():
            channel = Channel.query.filter_by(channel_id=channel_id).first()
            if channel:
                db.session.delete(channel)
                db.session.commit()
                print(f"Channel {channel_id} deleted successfully.")
            else:
                print(f"Channel {channel_id} not found.")

    def update_channel(self, channel_id, button_name, subscription_link):
        with app.app_context():
            channel = Channel.query.filter_by(channel_id=channel_id).first()
            if channel:
                channel.button_name = button_name
                channel.subscription_link = subscription_link
                db.session.commit()
                print(f"Channel {channel_id} updated successfully.")
            else:
                print(f"Channel {channel_id} not found.")

if __name__ == "__main__":
    db_manager = DatabaseManager()
    # Uncomment and use these functions as needed
    # db_manager.init_db()
    # db_manager.add_user("testuser", "testpassword")
    # db_manager.list_users()
    # db_manager.list_channels()
    # db_manager.delete_user("testuser")
    # db_manager.delete_channel("example_channel_id")
    # db_manager.update_channel("example_channel_id", "New Button Name", "https://new.subscription.link")
    pass

__all__ = ['DatabaseManager']

