from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from models import db, User, Company, Role, Complaint, Repair, Replacement, Unit, Issue, AccountType,  Holiday, HolidayType
from app import bcrypt
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)

    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    companies = Company.query.all()
    roles = Role.query.all()
    complaints = Complaint.query.all()
    repairs = Repair.query.all()
    replacements = Replacement.query.all()
    units = Unit.query.all()
    issues = Issue.query.all()

    # Get count of each type by company
    company_stats = []
    for company in companies:
        company_users = User.query.filter_by(company_id=company.id).count()
        company_complaints = Complaint.query.filter_by(company_id=company.id).count()
        company_issues = Issue.query.filter_by(company_id=company.id).count()
        company_repairs = Repair.query.filter_by(company_id=company.id).count()
        company_replacements = Replacement.query.filter_by(company_id=company.id).count()
        company_units = Unit.query.filter_by(company_id=company.id).count()

        company_stats.append({
            'name': company.name,
            'users': company_users,
            'complaints': company_complaints,
            'issues': company_issues,
            'repairs': company_repairs,
            'replacements': company_replacements,
            'units': company_units
        })

    return render_template('admin/dashboard.html',
                           users=users,
                           companies=companies,
                           roles=roles,
                           complaints=complaints,
                           issues=issues,
                           repairs=repairs,
                           replacements=replacements,
                           units=units,
                           company_stats=company_stats)

# Admin routes for units
@admin_bp.route('/units')
@login_required
@admin_required
def admin_units():
    units = Unit.query.all()
    return render_template('admin/units.html', units=units)

@admin_bp.route('/edit_unit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_unit(id):
    unit = Unit.query.get_or_404(id)
    companies = Company.query.all()

    if request.method == 'POST':
        unit.unit_number = request.form['unit_number']
        unit.description = request.form['description']
        unit.floor = request.form['floor'] or None
        unit.building = request.form['building']
        unit.company_id = request.form['company_id']
        unit.is_occupied = 'is_occupied' in request.form

        # Update new fields
        toilet_count = request.form.get('toilet_count') or None
        towel_count = request.form.get('towel_count') or None
        max_pax = request.form.get('max_pax') or None

        # Convert to integers if not None
        if toilet_count:
            unit.toilet_count = int(toilet_count)
        else:
            unit.toilet_count = None

        if towel_count:
            unit.towel_count = int(towel_count)
        else:
            unit.towel_count = None

        if max_pax:
            unit.max_pax = int(max_pax)
        else:
            unit.max_pax = None

        db.session.commit()
        flash('Unit updated successfully', 'success')
        return redirect(url_for('admin.admin_units'))

    return render_template('admin/edit_unit.html', unit=unit, companies=companies)

@admin_bp.route('/delete_unit/<int:id>')
@login_required
@admin_required
def admin_delete_unit(id):
    unit = Unit.query.get_or_404(id)

    # Check if unit is in use
    if unit.complaints or unit.repairs or unit.replacements:
        flash('Cannot delete unit that is referenced by complaints, repairs, or replacements', 'danger')
        return redirect(url_for('admin.admin_units'))

    db.session.delete(unit)
    db.session.commit()

    flash('Unit deleted successfully', 'success')
    return redirect(url_for('admin.admin_units'))


@admin_bp.route('/add_unit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_unit():
    companies = Company.query.all()

    if request.method == 'POST':
        unit_number = request.form['unit_number']
        building = request.form.get('building')
        floor = request.form.get('floor')
        description = request.form.get('description')
        company_id = request.form['company_id']
        is_occupied = 'is_occupied' in request.form

        # Handle optional numeric fields
        toilet_count = request.form.get('toilet_count') or None
        towel_count = request.form.get('towel_count') or None
        max_pax = request.form.get('max_pax') or None

        # Convert to integers if not None
        if toilet_count:
            toilet_count = int(toilet_count)
        if towel_count:
            towel_count = int(towel_count)
        if max_pax:
            max_pax = int(max_pax)
        if floor:
            floor = int(floor)

        # Check if unit number already exists in this company
        existing_unit = Unit.query.filter_by(unit_number=unit_number, company_id=company_id).first()
        if existing_unit:
            flash('This unit number already exists in the selected company', 'danger')
            return render_template('admin/add_unit.html', companies=companies)

        new_unit = Unit(
            unit_number=unit_number,
            building=building,
            floor=floor,
            description=description,
            company_id=company_id,
            is_occupied=is_occupied,
            toilet_count=toilet_count,
            towel_count=towel_count,
            max_pax=max_pax
        )

        db.session.add(new_unit)
        db.session.commit()

        flash('Unit added successfully', 'success')
        return redirect(url_for('admin.admin_units'))

    return render_template('admin/add_unit.html', companies=companies)


# User management routes
@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    # Get all companies and roles for the form
    companies = Company.query.all()
    roles = Role.query.all()

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        company_id = request.form['company_id']
        role_id = request.form['role_id']
        is_cleaner = 'is_cleaner' in request.form  # Check if is_cleaner checkbox is checked

        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered', 'danger')
            return redirect(url_for('admin.admin_add_user'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Create new user without account_type_id
        new_user = User(
            name=name,
            email=email,
            password=hashed_password,
            company_id=company_id,
            role_id=role_id,
            is_cleaner=is_cleaner
        )

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully', 'success')
            return redirect(url_for('admin.admin_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding user: {str(e)}', 'danger')
            return redirect(url_for('admin.admin_add_user'))

    return render_template('admin/add_user.html', companies=companies, roles=roles)


@admin_bp.route('/edit_user/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(id):
    user = User.query.get_or_404(id)
    companies = Company.query.all()
    roles = Role.query.all()

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        user.company_id = request.form['company_id']
        user.role_id = request.form['role_id']
        user.is_cleaner = 'is_cleaner' in request.form  # Update is_cleaner field

        # Only update password if provided
        if request.form['password'].strip():
            user.password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')

        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.admin_users'))

    return render_template('admin/edit_user.html', user=user, companies=companies, roles=roles)

@admin_bp.route('/delete_user/<int:id>')
@login_required
@admin_required
def admin_delete_user(id):
    if id == current_user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.admin_users'))

    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.admin_users'))

# Company routes
@admin_bp.route('/companies')
@login_required
@admin_required
def admin_companies():
    companies = Company.query.all()
    return render_template('admin/companies.html', companies=companies)


@admin_bp.route('/add_company', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_company():
    if request.method == 'POST':
        name = request.form['name']
        max_units = request.form.get('max_units', 20)
        max_manager_users = request.form.get('max_manager_users', 1)
        max_staff_users = request.form.get('max_staff_users', 1)
        max_cleaner_users = request.form.get('max_cleaner_users', 2)

        # Validate inputs
        try:
            max_units = int(max_units)
            max_manager_users = int(max_manager_users)
            max_staff_users = int(max_staff_users)
            max_cleaner_users = int(max_cleaner_users)

            if max_units < 15 or max_units > 1000:
                flash('Unit limit must be between 15 and 1000', 'danger')
                return render_template('admin/add_company.html')

            if max_manager_users < 1 or max_staff_users < 0 or max_cleaner_users < 0:
                flash('Manager limit must be at least 1, other limits must be non-negative', 'danger')
                return render_template('admin/add_company.html')

        except ValueError:
            flash('Invalid values provided', 'danger')
            return render_template('admin/add_company.html')

        # Check if company already exists
        company = Company.query.filter_by(name=name).first()
        if company:
            flash('Company already exists', 'danger')
            return redirect(url_for('admin.admin_add_company'))

        new_company = Company(
            name=name,
            max_units=max_units,
            max_manager_users=max_manager_users,
            max_staff_users=max_staff_users,
            max_cleaner_users=max_cleaner_users
        )
        db.session.add(new_company)
        db.session.commit()

        flash('Company added successfully', 'success')
        return redirect(url_for('admin.admin_companies'))

    return render_template('admin/add_company.html')


@admin_bp.route('/edit_company/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_company(id):
    company = Company.query.get_or_404(id)

    if request.method == 'POST':
        company.name = request.form['name']
        max_units = request.form.get('max_units', company.max_units)
        max_manager_users = request.form.get('max_manager_users', company.max_manager_users)
        max_staff_users = request.form.get('max_staff_users', company.max_staff_users)
        max_cleaner_users = request.form.get('max_cleaner_users', company.max_cleaner_users)

        # Validate inputs
        try:
            max_units = int(max_units)
            max_manager_users = int(max_manager_users)
            max_staff_users = int(max_staff_users)
            max_cleaner_users = int(max_cleaner_users)

            if max_units < 15 or max_units > 1000:
                flash('Unit limit must be between 15 and 1000', 'danger')
                return render_template('admin/edit_company.html', company=company)

            if max_manager_users < 1:
                flash('Manager limit must be at least 1', 'danger')
                return render_template('admin/edit_company.html', company=company)

        except ValueError:
            flash('Invalid values provided', 'danger')
            return render_template('admin/edit_company.html', company=company)

        # Check if reducing limits below current user count
        current_units = Unit.query.filter_by(company_id=company.id).count()
        if max_units < current_units:
            flash(f'Cannot set unit limit to {max_units}. Company currently has {current_units} units.', 'danger')
            return render_template('admin/edit_company.html', company=company)

        # Check user limits
        current_managers = company.get_user_count_by_role('Manager')
        current_staff = company.get_user_count_by_role('Staff')
        current_cleaners = company.get_user_count_by_role('Cleaner')

        if max_manager_users < current_managers:
            flash(
                f'Cannot set Manager limit to {max_manager_users}. Company currently has {current_managers} Managers.',
                'danger')
            return render_template('admin/edit_company.html', company=company)

        if max_staff_users < current_staff:
            flash(f'Cannot set Staff limit to {max_staff_users}. Company currently has {current_staff} Staff.',
                  'danger')
            return render_template('admin/edit_company.html', company=company)

        if max_cleaner_users < current_cleaners:
            flash(
                f'Cannot set Cleaner limit to {max_cleaner_users}. Company currently has {current_cleaners} Cleaners.',
                'danger')
            return render_template('admin/edit_company.html', company=company)

        # Update company
        company.max_units = max_units
        company.max_manager_users = max_manager_users
        company.max_staff_users = max_staff_users
        company.max_cleaner_users = max_cleaner_users

        db.session.commit()
        flash('Company updated successfully', 'success')
        return redirect(url_for('admin.admin_companies'))

    return render_template('admin/edit_company.html', company=company)


@admin_bp.route('/delete_company/<int:id>')
@login_required
@admin_required
def admin_delete_company(id):
    company = Company.query.get_or_404(id)

    # Check if company has users or units
    if company.users or company.units:
        flash('Cannot delete company with existing users or units', 'danger')
        return redirect(url_for('admin.admin_companies'))

    db.session.delete(company)
    db.session.commit()

    flash('Company deleted successfully', 'success')
    return redirect(url_for('admin.admin_companies'))

# Role routes
@admin_bp.route('/roles')
@login_required
@admin_required
def admin_roles():
    roles = Role.query.all()
    return render_template('admin/roles.html', roles=roles)

@admin_bp.route('/add_role', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_role():
    if request.method == 'POST':
        name = request.form['name']

        # Check if role already exists
        role = Role.query.filter_by(name=name).first()
        if role:
            flash('Role already exists', 'danger')
            return redirect(url_for('admin.admin_add_role'))

        # Create new role with permissions
        new_role = Role(
            name=name,
            can_view_issues='can_view_issues' in request.form,
            can_manage_issues='can_manage_issues' in request.form,
            can_view_bookings='can_view_bookings' in request.form,
            can_manage_bookings='can_manage_bookings' in request.form,
            can_view_calendar='can_view_calendar' in request.form,
            can_manage_calendar='can_manage_calendar' in request.form,
            can_view_occupancy='can_view_occupancy' in request.form,
            can_manage_occupancy='can_manage_occupancy' in request.form,
            can_view_expenses='can_view_expenses' in request.form,
            can_manage_expenses='can_manage_expenses' in request.form,
            can_view_contacts='can_view_contacts' in request.form,
            can_manage_contacts='can_manage_contacts' in request.form,
            can_view_analytics='can_view_analytics' in request.form,
            can_manage_analytics='can_manage_analytics' in request.form,
            can_view_units='can_view_units' in request.form,
            can_manage_units='can_manage_units' in request.form,
            can_view_manage_cleaners='can_view_manage_cleaners' in request.form,
            can_manage_manage_cleaners='can_manage_manage_cleaners' in request.form,
            can_view_jadual_pembersihan='can_view_jadual_pembersihan' in request.form,
            can_manage_jadual_pembersihan='can_manage_jadual_pembersihan' in request.form,
            is_admin='is_admin' in request.form,
            can_manage_users='can_manage_users' in request.form
        )

        db.session.add(new_role)
        db.session.commit()

        flash('Role added successfully', 'success')
        return redirect(url_for('admin.admin_roles'))

    return render_template('admin/add_role.html')

@admin_bp.route('/edit_role/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_role(id):
    role = Role.query.get_or_404(id)

    if request.method == 'POST':
        role.name = request.form['name']

        # Update permissions

        role.can_view_issues = 'can_view_issues' in request.form
        role.can_manage_issues = 'can_manage_issues' in request.form
        role.can_view_bookings = 'can_view_bookings' in request.form
        role.can_manage_bookings = 'can_manage_bookings' in request.form
        role.can_view_calendar = 'can_view_calendar' in request.form
        role.can_manage_calendar = 'can_manage_calendar' in request.form
        role.can_view_occupancy = 'can_view_occupancy' in request.form
        role.can_manage_occupancy = 'can_manage_occupancy' in request.form
        role.can_view_expenses = 'can_view_expenses' in request.form
        role.can_manage_expenses = 'can_manage_expenses' in request.form
        role.can_view_contacts = 'can_view_contacts' in request.form
        role.can_manage_contacts = 'can_manage_contacts' in request.form
        role.can_view_analytics = 'can_view_analytics' in request.form
        role.can_manage_analytics = 'can_manage_analytics' in request.form
        role.can_view_units = 'can_view_units' in request.form
        role.can_manage_units = 'can_manage_units' in request.form
        role.can_view_manage_cleaners = 'can_view_manage_cleaners' in request.form
        role.can_manage_manage_cleaners = 'can_manage_manage_cleaners' in request.form
        role.can_view_jadual_pembersihan = 'can_view_jadual_pembersihan' in request.form
        role.can_manage_jadual_pembersihan = 'can_manage_jadual_pembersihan' in request.form
        role.is_admin = 'is_admin' in request.form
        role.can_manage_users = 'can_manage_users' in request.form

        db.session.commit()
        flash('Role updated successfully', 'success')
        return redirect(url_for('admin.admin_roles'))

    return render_template('admin/edit_role.html', role=role)

@admin_bp.route('/delete_role/<int:id>')
@login_required
@admin_required
def admin_delete_role(id):
    role = Role.query.get_or_404(id)

    # Check if role has users
    if role.users:
        flash('Cannot delete role with existing users', 'danger')
        return redirect(url_for('admin.admin_roles'))

    db.session.delete(role)
    db.session.commit()

    flash('Role deleted successfully', 'success')
    return redirect(url_for('admin.admin_roles'))

@admin_bp.route('/complaints')
@login_required
@admin_required
def admin_complaints():
    complaints = Complaint.query.all()
    return render_template('admin/complaints.html', complaints=complaints)

@admin_bp.route('/repairs')
@login_required
@admin_required
def admin_repairs():
    repairs = Repair.query.all()
    return render_template('admin/repairs.html', repairs=repairs)

@admin_bp.route('/replacements')
@login_required
@admin_required
def admin_replacements():
    replacements = Replacement.query.all()
    return render_template('admin/replacements.html', replacements=replacements)


# Holiday management routes for admin.py

@admin_bp.route('/holidays')
@login_required
@admin_required
def admin_holidays():
    holiday_types = HolidayType.query.all()
    holidays = Holiday.query.all()
    return render_template('admin/holidays.html', holiday_types=holiday_types, holidays=holidays)


@admin_bp.route('/add_holiday_type', methods=['GET', 'POST'])
@login_required
@admin_required
def add_holiday_type():
    if request.method == 'POST':
        name = request.form['name']
        color = request.form['color']

        # Check if holiday type already exists
        existing_type = HolidayType.query.filter_by(name=name).first()
        if existing_type:
            flash('Holiday type already exists', 'danger')
            return redirect(url_for('admin.add_holiday_type'))

        new_holiday_type = HolidayType(
            name=name,
            color=color,
            is_system=False
        )

        db.session.add(new_holiday_type)
        db.session.commit()

        flash('Holiday type added successfully', 'success')
        return redirect(url_for('admin.admin_holidays'))

    return render_template('admin/add_holiday_type.html')


@admin_bp.route('/edit_holiday_type/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_holiday_type(id):
    holiday_type = HolidayType.query.get_or_404(id)

    # Prevent editing system types
    if holiday_type.is_system:
        flash('System holiday types cannot be edited', 'danger')
        return redirect(url_for('admin.admin_holidays'))

    if request.method == 'POST':
        holiday_type.name = request.form['name']
        holiday_type.color = request.form['color']

        db.session.commit()
        flash('Holiday type updated successfully', 'success')
        return redirect(url_for('admin.admin_holidays'))

    return render_template('admin/edit_holiday_type.html', holiday_type=holiday_type)


@admin_bp.route('/delete_holiday_type/<int:id>')
@login_required
@admin_required
def delete_holiday_type(id):
    holiday_type = HolidayType.query.get_or_404(id)

    # Prevent deleting system types
    if holiday_type.is_system:
        flash('System holiday types cannot be deleted', 'danger')
        return redirect(url_for('admin.admin_holidays'))

    # Check if any holidays use this type
    if holiday_type.holidays:
        flash('Cannot delete holiday type that is in use', 'danger')
        return redirect(url_for('admin.admin_holidays'))

    db.session.delete(holiday_type)
    db.session.commit()

    flash('Holiday type deleted successfully', 'success')
    return redirect(url_for('admin.admin_holidays'))


@admin_bp.route('/add_holiday', methods=['GET', 'POST'])
@login_required
@admin_required
def add_holiday():
    holiday_types = HolidayType.query.all()

    if request.method == 'POST':
        name = request.form['name']
        date_str = request.form['date']
        holiday_type_id = request.form['holiday_type_id']
        is_recurring = 'is_recurring' in request.form

        # Convert date string to date object
        holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Create new holiday
        new_holiday = Holiday(
            name=name,
            date=holiday_date,
            holiday_type_id=holiday_type_id,
            is_recurring=is_recurring
        )

        db.session.add(new_holiday)
        db.session.commit()

        flash('Holiday added successfully', 'success')
        return redirect(url_for('admin.admin_holidays'))

    return render_template('admin/add_holiday.html', holiday_types=holiday_types)


@admin_bp.route('/edit_holiday/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_holiday(id):
    holiday = Holiday.query.get_or_404(id)
    holiday_types = HolidayType.query.all()

    if request.method == 'POST':
        holiday.name = request.form['name']
        holiday.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
        holiday.holiday_type_id = request.form['holiday_type_id']
        holiday.is_recurring = 'is_recurring' in request.form

        db.session.commit()
        flash('Holiday updated successfully', 'success')
        return redirect(url_for('admin.admin_holidays'))

    return render_template('admin/edit_holiday.html', holiday=holiday, holiday_types=holiday_types)


@admin_bp.route('/delete_holiday/<int:id>')
@login_required
@admin_required
def delete_holiday(id):
    holiday = Holiday.query.get_or_404(id)

    db.session.delete(holiday)
    db.session.commit()

    flash('Holiday deleted successfully', 'success')
    return redirect(url_for('admin.admin_holidays'))



@admin_bp.route('/system_holidays')
@login_required
@admin_required
def system_holidays():
    # Get all holiday types
    holiday_types = HolidayType.query.all()

    # Get system-wide holidays (where company_id is None)
    public_holidays = Holiday.query.filter_by(
        holiday_type_id=HolidayType.query.filter_by(name="Malaysia Public Holiday").first().id,
        company_id=None
    ).order_by(Holiday.date).all()

    school_holidays = Holiday.query.filter_by(
        holiday_type_id=HolidayType.query.filter_by(name="Malaysia School Holiday").first().id,
        company_id=None
    ).order_by(Holiday.date).all()

    return render_template('admin/system_holidays.html',
                           holiday_types=holiday_types,
                           public_holidays=public_holidays,
                           school_holidays=school_holidays)


@admin_bp.route('/add_system_holiday', methods=['POST'])
@login_required
@admin_required
def add_system_holiday():
    name = request.form['name']
    date_str = request.form['date']
    holiday_type_id = request.form['holiday_type_id']
    is_recurring = 'is_recurring' in request.form

    # Convert date string to date object
    holiday_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    # Check if holiday already exists
    existing_holiday = Holiday.query.filter_by(
        date=holiday_date,
        holiday_type_id=holiday_type_id,
        company_id=None
    ).first()

    if existing_holiday:
        flash('Holiday already exists for this date and type', 'danger')
    else:
        # Create system-wide holiday
        new_holiday = Holiday(
            name=name,
            date=holiday_date,
            holiday_type_id=holiday_type_id,
            company_id=None,  # System-wide holiday
            is_recurring=is_recurring,
            is_deleted=False
        )

        db.session.add(new_holiday)
        db.session.commit()

        flash('System-wide holiday added successfully', 'success')

    return redirect(url_for('admin.system_holidays'))


@admin_bp.route('/delete_system_holiday/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_system_holiday(id):
    holiday = Holiday.query.get_or_404(id)

    # Ensure this is a system-wide holiday
    if holiday.company_id is not None:
        flash('This is not a system-wide holiday', 'danger')
        return redirect(url_for('admin.system_holidays'))

    # Delete the holiday
    db.session.delete(holiday)
    db.session.commit()

    flash('System-wide holiday deleted successfully', 'success')
    return redirect(url_for('admin.system_holidays'))