from flask import Flask, render_template, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
import os
import pytz
from models import db, User, Role, Company, AccountType, HolidayType
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_apscheduler import APScheduler

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///propertyhub.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

# Initialize extensions
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

# Initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)


# Add template filter for Malaysia timezone
@app.template_filter('malaysia_time')
def malaysia_time_filter(utc_dt):
    """Convert UTC datetime to Malaysia timezone"""
    if utc_dt is None:
        return ""
    malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
    if utc_dt.tzinfo is None:
        utc_dt = pytz.utc.localize(utc_dt)
    malaysia_time = utc_dt.astimezone(malaysia_tz)
    return malaysia_time.strftime('%b %d, %Y, %I:%M %p')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Function to create default roles and a default company
def create_default_data():
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        # Create account types first
        create_account_types()

        # Check if default company exists
        default_company = Company.query.filter_by(name="Default Company").first()
        if not default_company:
            # Get standard account type
            standard_account = AccountType.query.filter_by(name="Standard Account").first()

            default_company = Company(
                name="Default Company",
                account_type_id=standard_account.id if standard_account else 1
            )
            db.session.add(default_company)
            db.session.commit()
            print("Default company created")

        # Create default roles if they don't exist
        roles = {
            "Admin": {
                "can_view_complaints": True,
                "can_manage_complaints": True,
                "can_view_issues": True,
                "can_manage_issues": True,
                "can_view_repairs": True,
                "can_manage_repairs": True,
                "can_view_replacements": True,
                "can_manage_replacements": True,
                "can_view_bookings": True,
                "can_manage_bookings": True,
                "can_view_calendar": True,
                "can_manage_calendar": True,
                "can_view_occupancy": True,
                "can_manage_occupancy": True,
                "can_view_expenses": True,
                "can_manage_expenses": True,
                "can_view_contacts": True,
                "can_manage_contacts": True,
                "can_view_analytics": True,
                "can_manage_analytics": True,
                "can_view_units": True,
                "can_manage_units": True,
                "can_view_manage_cleaners": True,
                "can_manage_manage_cleaners": True,
                "can_view_jadual_pembersihan": True,
                "can_manage_jadual_pembersihan": True,
                "is_admin": True,
                "can_manage_users": True
            },
            "Manager": {
                "can_view_complaints": True,
                "can_manage_complaints": True,
                "can_view_issues": True,
                "can_manage_issues": True,
                "can_view_repairs": True,
                "can_manage_repairs": True,
                "can_view_replacements": True,
                "can_manage_replacements": True,
                "can_view_bookings": True,
                "can_manage_bookings": True,
                "can_view_calendar": True,
                "can_manage_calendar": True,
                "can_view_occupancy": True,
                "can_manage_occupancy": True,
                "can_view_expenses": True,
                "can_manage_expenses": True,
                "can_view_contacts": True,
                "can_manage_contacts": True,
                "can_view_analytics": True,
                "can_manage_analytics": True,
                "can_view_units": True,
                "can_manage_units": True,
                "can_view_manage_cleaners": True,
                "can_manage_manage_cleaners": True,
                "can_view_jadual_pembersihan": True,
                "can_manage_jadual_pembersihan": True,
                "is_admin": False,
                "can_manage_users": False
            },
            "Staff": {
                "can_view_complaints": True,
                "can_manage_complaints": False,
                "can_view_issues": True,
                "can_manage_issues": True,
                "can_view_repairs": True,
                "can_manage_repairs": False,
                "can_view_replacements": True,
                "can_manage_replacements": False,
                "can_view_bookings": True,
                "can_manage_bookings": True,
                "can_view_calendar": True,
                "can_manage_calendar": False,
                "can_view_occupancy": True,
                "can_manage_occupancy": False,
                "can_view_expenses": True,
                "can_manage_expenses": False,
                "can_view_contacts": True,
                "can_manage_contacts": False,
                "can_view_analytics": True,
                "can_manage_analytics": False,
                "can_view_units": True,
                "can_manage_units": False,
                "can_view_manage_cleaners": False,
                "can_manage_manage_cleaners": False,
                "can_view_jadual_pembersihan": True,
                "can_manage_jadual_pembersihan": False,
                "is_admin": False,
                "can_manage_users": False
            },
            "Technician": {
                "can_view_complaints": True,
                "can_manage_complaints": False,
                "can_view_repairs": True,
                "can_manage_repairs": True,
                "can_view_replacements": False,
                "can_manage_replacements": False,
                "is_admin": False,
                "can_manage_users": False
            },
            "Cleaner": {
                "can_view_complaints": True,
                "can_manage_complaints": False,
                "can_view_issues": True,
                "can_manage_issues": False,
                "can_view_repairs": False,
                "can_manage_repairs": False,
                "can_view_replacements": True,
                "can_manage_replacements": True,
                "can_view_jadual_pembersihan": True,
                "can_manage_jadual_pembersihan": False,
                "is_admin": False,
                "can_manage_users": False
            }
        }

        for role_name, permissions in roles.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(name=role_name, **permissions)
                db.session.add(role)
                db.session.commit()
                print(f"Role '{role_name}' created")

        # Create admin user if no admin exists
        admin_role = Role.query.filter_by(name="Admin").first()
        admin = User.query.filter_by(is_admin=True).first()

        if not admin and admin_role:
            password = 'admin123'  # Default password
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            admin = User(
                name='Admin',
                email='admin@example.com',
                password=hashed_password,
                role_id=admin_role.id,
                company_id=default_company.id
            )
            db.session.add(admin)
            db.session.commit()
            print('Admin user created with email: admin@example.com and password: admin123')

        # Create a few sample units for the default company
        from models import Unit
        if Unit.query.count() == 0:
            sample_units = [
                {"unit_number": "A-101", "building": "Block A", "floor": 1, "description": "Corner unit",
                 "is_occupied": True},
                {"unit_number": "A-102", "building": "Block A", "floor": 1, "description": "Middle unit",
                 "is_occupied": True},
                {"unit_number": "B-201", "building": "Block B", "floor": 2, "description": "End unit",
                 "is_occupied": True},
                {"unit_number": "C-301", "building": "Block C", "floor": 3, "description": "Penthouse",
                 "is_occupied": False},
            ]

            for unit_data in sample_units:
                unit = Unit(
                    unit_number=unit_data["unit_number"],
                    building=unit_data["building"],
                    floor=unit_data["floor"],
                    description=unit_data["description"],
                    is_occupied=unit_data["is_occupied"],
                    company_id=default_company.id
                )
                db.session.add(unit)

            db.session.commit()
            print("Default data created successfully")
        else:
            print("Default data already exists")

    # Call the create_issue_defaults function
    create_issue_defaults()

    # Add the create_cleaner_role function definition here
    def create_cleaner_role():
        # Check if Cleaner role exists
        cleaner_role = Role.query.filter_by(name="Cleaner").first()
        if not cleaner_role:
            cleaner_role = Role(
                name="Cleaner",
                can_view_complaints=True,
                can_manage_complaints=False,
                can_view_issues=True,
                can_manage_issues=False,
                can_view_repairs=False,
                can_manage_repairs=False,
                can_view_replacements=False,
                can_manage_replacements=False,
                is_admin=False,
                can_manage_users=False
            )
            db.session.add(cleaner_role)
            db.session.commit()
            print("Cleaner role created")

    # Add this code to the create_default_data function in app.py

    def create_holiday_types():
        # Check if holiday types exist
        if HolidayType.query.count() == 0:
            # Create default holiday types
            holiday_types = [
                {"name": "Malaysia Public Holiday", "color": "#4CAF50", "is_system": True},
                {"name": "Malaysia School Holiday", "color": "#2196F3", "is_system": True},
                {"name": "Custom Holiday", "color": "#9C27B0", "is_system": True}
            ]

            for type_data in holiday_types:
                holiday_type = HolidayType(
                    name=type_data["name"],
                    color=type_data["color"],
                    is_system=type_data["is_system"]
                )
                db.session.add(holiday_type)

            db.session.commit()
            print("Default holiday types created")


    # Call the function at the end of create_default_data
    create_cleaner_role()
    create_holiday_types()


def create_account_types():
    # Check if account types exist
    if AccountType.query.count() == 0:
        account_types = [
            {"name": "Standard Account", "max_units": 20},
            {"name": "Premium Account", "max_units": 40},
            {"name": "Pro Account", "max_units": 80},
            {"name": "Elite Account", "max_units": 160},
            {"name": "Ultimate Account", "max_units": 2000}
        ]

        for type_data in account_types:
            account_type = AccountType(
                name=type_data["name"],
                max_units=type_data["max_units"]
            )
            db.session.add(account_type)

        db.session.commit()
        print("Account types created")


def create_issue_items():
    # Define issue items by category
    from models import Category, IssueItem
    issue_items_by_category = {
        "Building Issue": [
            "Carpark - Not Enough",
            "Carpark - Too High",
            "Lift - Waiting too long",
            "Swimming pool",
            "Noisy neighbour"
        ],
        "Cleaning Issue": [
            "Dusty",
            "Bedsheet - Not Clean",
            "Bedsheet - Smelly",
            "Toilet - Smelly",
            "Toilet Not Clean",
            "House - Smelly",
            "Got Ants",
            "Got Cockroach",
            "Got Insects",
            "Got mouse",
            "Not enough towels",
            "Not enough toiletries"
        ],
        "Plumbing Issues": [
            "Basin stucked",
            "Basin dripping",
            "Faucet Dripping",
            "Bidet dripping",
            "Toilet bowl stuck",
            "Shower head",
            "Toilet fitting lose",
            "Water pressure Low",
            "Drainage problem"
        ],
        "Electrical Issue": [
            "TV Box",
            "Internet WiFi",
            "Water Heater",
            "Fan",
            "Washing machine",
            "House No Electric",
            "Light",
            "Hair dryer",
            "Iron",
            "Microwave",
            "Kettle",
            "Remote control",
            "Induction Cooker",
            "Rice Cooker",
            "Water Filter",
            "Fridge"
        ],
        "Furniture Issue": [
            "Chair",
            "Sofa",
            "Wardrobe",
            "Kitchenware",
            "Bed",
            "Pillow",
            "Bedframe",
            "Iron board Cover",
            "Windows",
            "Coffee Table",
            "Cabinet",
            "Dining Table"
        ],
        "Check-in Issue": [
            "Access card Holder",
            "Access card",
            "key",
            "Letterbox - cant open",
            "Letterbox - left open",
            "Letterbox - missing",
            "Door",
            "Door Password"
        ],
        "Aircond Issue": [
            "AC not cold",
            "AC leaking",
            "AC noisy",
            "AC empty - tank"
        ]
    }

    # Get or create categories
    for category_name, items in issue_items_by_category.items():
        # Get or create the category
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.flush()  # Flush to get the category ID

        # Create issue items for this category
        for item_name in items:
            # Check if the issue item already exists
            existing_item = IssueItem.query.filter_by(name=item_name, category_id=category.id).first()
            if not existing_item:
                issue_item = IssueItem(name=item_name, category_id=category.id)
                db.session.add(issue_item)

    db.session.commit()
    print("Issue items created successfully")


def create_issue_defaults():
    # Create categories
    from models import Category, ReportedBy, Priority, Status, Type, IssueItem

    categories = ["Building Issue", "Cleaning Issue", "Plumbing Issues", "Electrical Issue", "Furniture Issue",
                  "Check-in Issue", "Aircond Issue"]
    for category_name in categories:
        if not Category.query.filter_by(name=category_name).first():
            category = Category(name=category_name)
            db.session.add(category)

    # Create reported by options
    reporters = ["Cleaner", "Guest", "Operator", "Head"]
    for reporter_name in reporters:
        if not ReportedBy.query.filter_by(name=reporter_name).first():
            reporter = ReportedBy(name=reporter_name)
            db.session.add(reporter)

    # Create priorities
    priorities = ["High", "Medium", "Low"]
    for priority_name in priorities:
        if not Priority.query.filter_by(name=priority_name).first():
            priority = Priority(name=priority_name)
            db.session.add(priority)

    # Create statuses
    statuses = ["Pending", "In Progress", "Resolved", "Rejected"]
    for status_name in statuses:
        if not Status.query.filter_by(name=status_name).first():
            status = Status(name=status_name)
            db.session.add(status)

    # Create types
    types = ["Repair", "Replace"]
    for type_name in types:
        if not Type.query.filter_by(name=type_name).first():
            type_obj = Type(name=type_name)
            db.session.add(type_obj)

    db.session.commit()

    # Create the issue items
    create_issue_items()
    print("Issue defaults created")


def sync_all_calendars():
    """Sync all active calendar sources that have URLs"""
    import requests
    from models import CalendarSource
    from routes.calendar import process_ics_calendar

    # Get all active calendar sources with URLs
    calendar_sources = CalendarSource.query.filter(
        CalendarSource.source_url.isnot(None),
        CalendarSource.is_active == True
    ).all()

    for source in calendar_sources:
        try:
            # Download the ICS file
            response = requests.get(source.source_url)
            if response.status_code == 200:
                calendar_data = response.text
                # Process the calendar with the source identifier
                process_ics_calendar(
                    calendar_data,
                    source.unit_id,
                    source.source_name,
                    source.source_identifier
                )
                # Update the last_updated timestamp
                source.last_updated = datetime.utcnow()
                db.session.commit()
                print(f"Successfully synced {source.source_identifier} for unit {source.unit.unit_number}")
        except Exception as e:
            print(f"Error syncing calendar for {source.unit.unit_number} from {source.source_identifier}: {str(e)}")
            # Optionally, you could disable problematic sources after several failures
            # source.is_active = False
            # db.session.commit()


def init_scheduler(app):
    scheduler.init_app(app)
    scheduler.start()

    # Schedule the sync task to run every day at 2 AM
    scheduler.add_job(func=sync_all_calendars, trigger='cron', hour=2, id='sync_calendars')
    ## Schedule the sync task to run every minute
    # scheduler.add_job(
    #    func=sync_all_calendars,
    #    trigger='interval',
    #    minutes=1,
    #    id='sync_calendars'
    # )


# Import and register blueprints
from routes import register_blueprints

register_blueprints(app)

# Create the database tables
with app.app_context():
    db.create_all()
    create_default_data()
    create_account_types()
    init_scheduler(app)

if __name__ == '__main__':
    app.run(debug=True)

