from flask import render_template, redirect, url_for, flash, request
from werkzeug.utils import secure_filename
import os

# ...existing imports...

@main.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm()
    
    if form.validate_on_submit():
        item.name = form.name.data
        item.description = form.description.data
        
        if form.image.data:
            # Delete old image if it exists
            if item.image_path:
                old_image_path = os.path.join(current_app.root_path, 'static', item.image_path)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            
            # Save new image
            filename = secure_filename(form.image.data.filename)
            file_path = os.path.join('uploads', filename)
            form.image.data.save(os.path.join(current_app.root_path, 'static', file_path))
            item.image_path = file_path
        
        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('main.view_box', box_id=item.box_id))
    
    # Pre-populate form with existing data
    if request.method == 'GET':
        form.name.data = item.name
        form.description.data = item.description
    
    return render_template('edit_item.html', form=form, item=item)
