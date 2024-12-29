import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, send_file, Response
from werkzeug.utils import secure_filename
from .models import db, Box, Item
from .forms import BoxForm, ItemForm
from .utils import generate_qr_code, generate_qr_id, export_to_csv
from datetime import datetime

main = Blueprint('main', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@main.route('/')
def index():
    boxes = Box.query.all()
    return render_template('index.html', boxes=boxes)

@main.route('/box/new', methods=['GET', 'POST'])
def new_box():
    form = BoxForm()
    if form.validate_on_submit():
        qr_code_id = generate_qr_id()
        box = Box(
            id=qr_code_id,
            name=form.name.data,
            description=form.description.data,
            location=form.location.data,
            qr_code_id=qr_code_id
        )
        db.session.add(box)
        db.session.commit()
        
        # Generate QR code after getting the box ID
        # qr_filename = f'box_{box.id}'
        # qr_filename = qr_code_id
        qr_data = f'http://localhost:5000/box/{box.id}'
        generate_qr_code(qr_data, qr_code_id)
        
        box.qr_code = f'qr_codes/{qr_code_id}.png'
        db.session.commit()
        
        flash('Box created successfully!', 'success')
        return redirect(url_for('main.view_box', box_id=box.id))
    return render_template('new_box.html', form=form)

@main.route('/add_box', methods=['GET', 'POST'])
def add_box():
    if request.method == 'POST':
        box_name = request.form.get('box_name')
        description = request.form.get('description')
        location = request.form.get('location')
        
        if box_name:
            new_box = Box(
                name=box_name,
                description=description,
                location=location
            )
            db.session.add(new_box)
            db.session.commit()
            flash('Box added successfully!', 'success')
            return redirect(url_for('main.index'))
            
    return render_template('add_box.html')

@main.route('/box/<string:box_id>')
def view_box(box_id):
    box = Box.query.get_or_404(box_id)
    return render_template('view_box.html', box=box)

@main.route('/box/<string:box_id>/item/new', methods=['GET', 'POST'])
def new_item(box_id):
    form = ItemForm()
    if form.validate_on_submit():
        item = Item(
            name=form.name.data,
            description=form.description.data,
            box_id=box_id
        )
        
        if form.image.data:
            file = form.image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                item.image_path = f'uploads/{filename}'
        
        db.session.add(item)
        db.session.commit()
        return redirect(url_for('main.view_box', box_id=box_id))
    
    return render_template('new_item.html', form=form, box_id=box_id)

@main.route('/box/<string:box_id>/edit', methods=['GET', 'POST'])
def edit_box(box_id):
    box = Box.query.get_or_404(box_id)
    form = BoxForm(obj=box)
    
    if form.validate_on_submit():
        box.name = form.name.data
        box.description = form.description.data
        db.session.commit()
        return redirect(url_for('main.view_box', box_id=box.id))
    
    return render_template('edit_box.html', form=form, box=box)

@main.route('/box/<string:box_id>/delete', methods=['POST'])
def delete_box(box_id):
    box = Box.query.get_or_404(box_id)
    
    # Delete associated QR code file
    if box.qr_code:
        qr_path = os.path.join(current_app.root_path, 'static', box.qr_code)
        if os.path.exists(qr_path):
            os.remove(qr_path)
    
    # Delete associated item images
    for item in box.items:
        if item.image_path:
            image_path = os.path.join(current_app.root_path, 'static', item.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
    
    db.session.delete(box)
    db.session.commit()
    return redirect(url_for('main.index'))

@main.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        
        if form.image.data:
            file = form.image.data
            if file and allowed_file(file.filename):
                # Delete old image if it exists
                if item.image_path:
                    old_image_path = os.path.join(current_app.root_path, 'static', item.image_path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(file.filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                item.image_path = f'uploads/{filename}'
        
        db.session.commit()
        return redirect(url_for('main.view_box', box_id=item.box_id))
    
    return render_template('edit_item.html', form=form, item=item)

@main.route('/item/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    box_id = item.box_id
    
    # Delete image file if it exists
    if item.image_path:
        image_path = os.path.join(current_app.root_path, 'static', item.image_path)
        if os.path.exists(image_path):
            os.remove(image_path)
    
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('main.view_box', box_id=box_id))

@main.route('/search')
def search():
    query = request.args.get('query', '')
    if query:
        # Search in items and join with boxes to get location
        search_results = Item.query.join(Box).filter(
            db.or_(
                Item.name.ilike(f'%{query}%'),
                Item.description.ilike(f'%{query}%'),
                Box.name.ilike(f'%{query}%'),
                Box.location.ilike(f'%{query}%')
            )
        ).all()
    else:
        search_results = []
    
    return render_template('search_results.html', results=search_results, query=query)

@main.route('/download/qr/<qr_code_id>')
def download_qr(qr_code_id):
    box = Box.query.filter_by(qr_code_id=qr_code_id).first_or_404()
    qr_path = os.path.join(current_app.root_path, 'static', 'qr_codes', f'{qr_code_id}.png')
    return send_file(qr_path, as_attachment=True)

@main.route('/export/csv')
def export_csv():
    boxes = Box.query.all()
    output = export_to_csv(boxes)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment;filename=garage_inventory_{datetime.now().strftime("%Y%m%d")}.csv'}
    )
