import os
from flask import Blueprint, request, jsonify, send_from_directory, current_app
from werkzeug.utils import secure_filename
from db import db
from models import Document, Scholar

documents_bp = Blueprint('documents', __name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'uploads')
ALLOWED_EXT   = {'pdf', 'docx', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/documents/<scholar_id>
# ─────────────────────────────────────────────────────────────────────────────
@documents_bp.route('/<int:scholar_id>', methods=['GET'])
def get_documents(scholar_id):
    docs = Document.query.filter_by(scholar_id=scholar_id)\
                         .order_by(Document.uploaded_at.desc()).all()
    return jsonify([d.to_dict() for d in docs]), 200


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/documents/upload   — multipart/form-data with file + scholar_id + category
# ─────────────────────────────────────────────────────────────────────────────
@documents_bp.route('/upload', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file       = request.files['file']
    scholar_id = request.form.get('scholar_id', type=int)
    category   = request.form.get('category', 'Other')

    if not file or file.filename == '':
        return jsonify({'error': 'Empty file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    ext  = filename.rsplit('.', 1)[1].upper()
    size = os.path.getsize(file_path)

    doc = Document(
        scholar_id=scholar_id,
        file_name=filename,
        file_path=f'/uploads/{filename}',
        file_type=ext,
        file_size=size,
        category=category,
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({'message': 'Uploaded', 'document': doc.to_dict()}), 201


# ─────────────────────────────────────────────────────────────────────────────
# DELETE /api/documents/<id>
# ─────────────────────────────────────────────────────────────────────────────
@documents_bp.route('/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    # Try to remove file from disk
    try:
        full = os.path.join(UPLOAD_FOLDER, doc.file_name)
        if os.path.exists(full):
            os.remove(full)
    except Exception:
        pass
    db.session.delete(doc)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200
