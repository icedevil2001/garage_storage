import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, send_file, Response
from werkzeug.utils import secure_filename
from .extensions import db
from .models import Box, Item
from .forms import BoxForm, ItemForm, BoxImageForm, SearchForm
from .utils import generate_qr_code, generate_qr_id, export_to_csv, resize_image, sequential_qr_id, image_hash, save_image_with_hash
from datetime import datetime
from pathlib import Path
import pandas as pd
from io import StringIO
from .llm_image_classification import llm_classification
from .utils import thumbnail_image
from flask import current_app as app


main = Blueprint('main', __name__)

COLUMNS = ["Box ID", "Box Name", "Box Location", "Item Name", "Description"]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@main.route('/')
def index():
    boxes = Box.query.all()
    return render_template('index.html', boxes=boxes)

@main.route('/box/new', methods=['GET', 'POST'])
def new_box():
    form = BoxForm()
    locations = Box.query.with_entities(Box.location).distinct().all()
    form.location.choices.extend([(name[0], name[0]) for name in locations])
    print(locations)
    # locations = Location.query.all()  # Fetch all locations
    app.logger.info(locations)
    if form.validate_on_submit():
        qr_code_id = sequential_qr_id()
        if Box.query.filter_by(qr_code_id=qr_code_id).first():
            flash('QR code ID already exists. Please try again.', 'danger')
            return redirect(url_for('main.new_box'))
        # print(form.new_location.data, form.location.data, form.data)
        # Check if the location is new and add it to the databas
        if form.location.data == '':
            location = form.new_location.data
        elif form.new_location.data:
            location = form.new_location.data
        else:
            location = form.location.data
        # location = form.new_location.data if len(form.new_location.data)>1 else form.location.data
        print(">>",location)
        box = Box(
            id=qr_code_id,
            name=form.name.data,
            description=form.description.data,
            location=location.title(),
            qr_code_id=qr_code_id,
            box_image=form.box_image.data

        )
        if form.box_image.data:
            file = form.box_image.data
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
                file.save(file_path)
                file_path = save_image_with_hash(file_path) # Save image with hash and resize
                # filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
                # file.save(filepath)
                # img = resize_image(filepath)
                # img.save(filepath) # Overwrite the original image with resized image
                # # thumbnail = resize_image(filepath, (128, 128))
                # img.thumbnail((128, 128))
                # img.save(Path(current_app.config['THUMBNAIL_FOLDER']) / filename)
                # # item.image_path = f'uploads/{filename}'
                box.box_image = str(current_app.config['UPLOAD_FOLDER'].relative_to(current_app.config['UPLOAD_FOLDER'].parents[0]) / filename)
        else:
            box.box_image = 'assets/Box.png'

        db.session.add(box)
        db.session.commit()
        
        qr_data = url_for('main.view_box', box_id=box.id, _external=True)
        generate_qr_code(qr_data, qr_code_id)
        
        box.qr_code = f'qr_codes/{qr_code_id}.png'
        db.session.commit()
        
        flash('Box created successfully!', 'success')
        return redirect(url_for('main.view_box', box_id=box.id))
    return render_template('new_box.html', form=form, locations=locations)

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

                file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
                file.save(file_path)
                file_path = save_image_with_hash(file_path) # Save image with hash and resize
                # filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
                # file.save(filepath)
                # img = resize_image(filepath)
                # img.save(filepath) # Overwrite the original image with resized image

                # img.thumbnail((128, 128))
                # img.save(Path(current_app.config['THUMBNAIL_FOLDER']) / filename)

                item.image_path = str(current_app.config['UPLOAD_FOLDER'].relative_to(current_app.config['UPLOAD_FOLDER'].parents[0]) / filename)
        
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
    root_path = Path(current_app.root_path)
    # Delete associated QR code file
    if box.qr_code:
        qr_path = root_path / 'static' / box.qr_code
        if os.path.exists(qr_path):
            os.remove(qr_path)
    
    # Delete associated item images
    for item in box.items:
        if item.image_path:
            image_path = root_path /'static' / item.image_path
            if os.path.exists(image_path):
                os.remove(image_path)
    
    db.session.delete(box)
    db.session.commit()
    flash('Box and all its items have been deleted!', 'success')
    return redirect(url_for('main.index'))

@main.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)
    root_path = Path(current_app.root_path)
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        
        if form.image.data:
            file = form.image.data
            if file and allowed_file(file.filename):
                # Delete old image if it exists
                if item.image_path:
                    old_image_path = root_path / 'static'/  item.image_path
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                filename = secure_filename(file.filename)
                file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
                file.save(file_path)
                file_path = save_image_with_hash(file_path) # Save image with hash and resize
                # filepath = Path(current_app.config['UPLOAD_FOLDER']) / filename
                # file.save(filepath)
                # img = resize_image(filepath)
                # img.save(filepath) # Overwrite the original image with resized image
                # # thumbnail = resize_image(filepath, (128, 128))
                # img.thumbnail((128, 128))
                # img.save(Path(current_app.config['THUMBNAIL_FOLDER']) / filename)
                item.image_path = f'uploads/{filename}'
        
        db.session.commit()
        return redirect(url_for('main.view_box', box_id=item.box_id))
    
    return render_template('edit_item.html', form=form, item=item)

@main.route('/item/<int:item_id>/delete', methods=['POST'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    box_id = item.box_id
    image_path = item.image_path
    db.session.delete(item)
    db.session.commit()
    # Delete image file if it exists

    ## image_path still exists in db dont delete image from folder
    item = Item.query.filter_by(image_path=image_path).first()
    if not item:
        image_path = Path(current_app.root_path) / 'static' / image_path
        if image_path.exists():
            image_path.unlink() 
    flash('Item has been deleted!', 'success')
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
    qr_path = Path(current_app.root_path) / 'static' / 'qr_codes' / f'{qr_code_id}.png'
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

@main.route('/box/<string:box_id>/classify', methods=['GET', 'POST'])
def classify_box_items_by_box_id(box_id):
    form = BoxImageForm()
    if form.validate_on_submit():
        try:
            if form.image.data:
                # Save the original image
                image = form.image.data
                _ai_classification(box_id, image)
                # filename = secure_filename(f"box_{box_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                # filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # image.save(filepath)
                
                # # Generate thumbnail
                # # thumb_filename = f"thumb_{filename}"
                # # thumb_path = os.path.join(app.config['UPLOAD_FOLDER'], thumb_filename)
                # # thumbnail_image(filepath, thumb_path)
                
                # # Classify items in the image
                # detected_items = llm_classification(filepath)
                
                # # Add items to database
                # for item in detected_items:
                #     new_item = Item(
                #         name=item['label'],
                #         box_id=box_id,
                #         image_path=filepath,
                #         # thumbnail=thumb_filename
                #     )
                #     db.session.add(new_item)
                #     app.logger.info(f'Item {item["label"]} added to box {box_id}')
                
                # db.session.commit()
                app.logger.info(f'Successfully classified items for box {box_id}')
                flash('Items have been classified and added to the box!', 'success')
        except Exception as e:
            app.logger.error(f'Error classifying items for box {box_id}: {str(e)}')
            flash('Error processing image classification', 'error')
        return redirect(url_for('main.view_box', box_id=box_id))
    
    return render_template('classify_items.html', form=form, box_id=box_id)

# @main.route('/box/<int:box_id>/download-csv-template')
@main.route('/box/download-csv-template')
def download_csv_template():
    # Get column names from Item table, excluding internal columns
    # columns = [column.name for column in Item.__table__.columns 
    #           if column.name not in ['id', 'box_id', 'image_path', 'created_at']]
    columns = COLUMNS
    
    # Create empty DataFrame with database columns
    df = pd.DataFrame(columns=columns)
    
    output = df.to_csv(index=False)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=items_template.csv'}
    )


@main.route('/batch-upload', methods=['GET', 'POST'])
def batch_upload():

    if request.method == 'POST':
        logger = app.logger.info('Batch upload started')
        if 'file' not in request.files:

            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        try:
            # Read file based on extension
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            if file_ext == 'csv':
                df = pd.read_csv(file)
            elif file_ext == 'tsv':
                df = pd.read_csv(file, sep='\t')
            elif file_ext in ['xls', 'xlsx']:
                df = pd.read_excel(file)
            else:
                flash('Unsupported file format. Please upload CSV, TSV or Excel file.', 'error')
                return redirect(request.url)
            app.logger.info(f'File read successfully with {len(df)} rows')
            app.logger.debug(f'Columns: {df.columns}')
            app.logger.debug(f'data: {df}')
            df = df.fillna('')  # Replace NaN with empty string 
            
            # Process each row
            for _, row in df.iterrows():
                # Create or get box
                box = Box.query.filter_by(qr_code_id=row['Box ID']).first()
                if not box:
                    box = Box(
                        id=row['Box ID'],
                        name=row['Box Name'],
                        location=row['Box Location'],
                        qr_code_id=row['Box ID']

                    )
                    db.session.add(box)
                    db.session.flush()  # Get box ID without committing

                    # Generate QR code
                    qr_data = url_for('main.view_box', box_id=box.id, _external=True)
                    generate_qr_code(qr_data, row['Box ID'])
                    box.qr_code = f'qr_codes/{row["Box ID"]}.png'

                # Create item
                if pd.notna(row['Item Name']):
                    item = Item.query.filter_by(name=row['Item Name'], box_id=box.id).first()
                    if not item:
                        item = Item(
                            name=row['Item Name'],
                            description=row.get('Description', ''),
                            box_id=box.id
                        )
                        db.session.add(item)

            db.session.commit()
            flash('Batch upload completed successfully!', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('batch_upload.html')


def _ai_classification(box_id, file):
    box = Box.query.get_or_404(box_id)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = Path(current_app.config['UPLOAD_FOLDER']) / filename
        file.save(file_path)
        file_path = save_image_with_hash(file_path) # Save image with hash and resize

        # filename = Path(secure_filename(file.filename))
        # ext = filename.suffix

        # file_path = current_app.config['UPLOAD_FOLDER'] / filename.name

        # file.save(file_path)
        # file_path: Path = current_app.config['UPLOAD_FOLDER'] / filename.name

        # resize_image(file_path).save(file_path)
        # new_filename: Path = current_app.config['UPLOAD_FOLDER'] / f"{image_hash(file_path)}{ext}"
        # file_path.rename(new_filename)
        # file_path = new_filename

        results = llm_classification(file_path)
        app.logger.info(f'AI Classification Results: {results}')
        for item in results:
            new_item = Item(
                name=item['label'],
                description=item.get('description', ''),
                box_id=box_id,
                image_path= f'uploads/{file_path.name}'
                # thumbnail=thumbnail_image(file_path)
            )
            db.session.add(new_item)
        db.session.commit()
        deteched_objects = [x['label'] for x in results]
        flash(f'AI Classification Results: {deteched_objects}', 'success')
        return redirect(url_for('main.view_box', box_id=box_id))
    flash('Invalid file type', 'danger')
    return redirect(request.url)

@main.route('/box/classify/', methods=['GET', 'POST'])
def classify_box_items():
    form = BoxImageForm()
    if form.validate_on_submit():
        try:
            box_id = form.box_name.data
            if form.image.data:
                _ai_classification(box_id, form.image.data)
                app.logger.info(f'Successfully classified items for box {box_id}')
                flash('Items have been classified and added to the box!', 'success')
                return redirect(url_for('main.view_box', box_id=box_id))

        except Exception as e:
            app.logger.error(f'Error classifying items for box {form.box_name[0]}: {str(e)}')
            flash('Error processing image classification', 'error')
        return redirect(url_for('main.view_box', box_id=box_id))
    
    return render_template('classify_items.html', form=form, box_id=form.box_name.data)


@main.route('/box/<string:box_id>/ai_classification', methods=['POST'])
def ai_classification(box_id):
    box = Box.query.get_or_404(box_id)
    if 'image' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        _ai_classification(box_id, file)
        # filename = secure_filename(file.filename)
        # file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # file.save(file_path)
        # results = llm_classification(file_path)
        # flash(f'AI Classification Results: {results}', 'success')
        return redirect(url_for('main.view_box', box_id=box.id))
    flash('Invalid file type', 'danger')
    return redirect(request.url)

# # @main.route('/location/new', methods=['GET', 'POST'])
# def add_location(location):
#     location = Location.query.filter_by(name=location).first()
#     if not location:
#         location = Location(name=location)
#         db.session.add(location)
#         db.session.commit()
#     return location.id


# @main.route('/location/new', methods=['GET', 'POST'])
# def new_location():
#     form = LocationForm()
#     if form.validate_on_submit():
#         location = Location.query.filter_by(name=form.location.data).first()
#         if not location:
#             location = Location(name=form.location.data)
#             db.session.add(location)
#             db.session.commit()
#             flash('Location added successfully!', 'success')
#             return redirect(url_for('main.index'))
#         flash('Location already exists.', 'danger')
#     return render_template('new_location.html', form=form)



# @main.route('/location/<string:location>/boxes')
# def get_location_boxes(location):
#     boxes = Box.query.filter_by(location=location ).all()
#     return render_template('index.html', boxes=boxes)


# @main.route('/location/<string:location>/items')
# def get_location_items(location):
#     items = Item.query.join(Box).filter(Box.location == location).all()
#     return render_template('items.html', items=items)

# @main.route('/location/add_defaults')
# def add_default_location():
#     locations = [
#         "N/A",
#         'Living Room',
#         'Bedroom',
#         'Kitchen',
#         'Bathroom',
#         'Garage',
#         'Attic',
#         'Basement',
#         'Storage Room'
#     ]
#     for location in locations:
#         results = Location.query.filter_by(name=location).first()
#         if not results:
#             loc_obj = Location(
#                 name=location)
#             db.session.add(loc_obj)
#             db.session.commit()
#     flash('Default locations added successfully!', 'success')
#     return redirect(url_for('main.index'))