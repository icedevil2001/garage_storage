from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, FileField, SubmitField, SelectField
from wtforms.validators import DataRequired
from app.models import Box

class BoxForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    location = SelectField('Location', choices=[
        ('',''),
        ('Living Room', 'Living Room'),
        ('Bedroom', 'Bedroom'),
        ('Kitchen', 'Kitchen'),
        ('Garage', 'Garage'),
        ('Storage', 'Storage'),
        ('Basement', 'Basement'),
        ('Attic', 'Attic'),
        ('Other', 'Other')
    ])
    new_location = StringField('New Location')
    box_image = FileField('Box Image', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg', 'HEIC'], 'Images only!')])
    submit = SubmitField('Create Box')

    # def __init__(self, *args, **kwargs):
    #     super(BoxForm, self).__init__(*args, **kwargs)
    #     self.location.choices = [(loc.id, loc.name) for loc in Location.query.all()]

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'HEIC'], 'Images only!')
    ])
    submit = SubmitField('Add Item')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class BoxImageForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(BoxImageForm, self).__init__(*args, **kwargs)
        self.box_name.choices = [(box.id, box.name) for box in Box.query.all()]

    box_name = SelectField('Box Name', validators=[DataRequired()])
    image = FileField('Box Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg','HEIC'], 'Images only!')
    ])
    submit = SubmitField('Classify Items')

class CSVUploadForm(FlaskForm):
    csv_file = FileField('CSV File', validators=[
        FileAllowed(['csv', 'tsv', 'xls','xlsx'], 'csv, tsv, xls, xlsx files only!')
    ])
    submit = SubmitField('Upload ')


class LocationForm(FlaskForm):
    location = StringField('Location', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Location')
