from models import db, User, Product, Report, Transaction, GlobalChatMessage, ProductImage
from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from werkzeug.security import generate_password_hash, check_password_hash
from models import ChatRoom, ChatMessage
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# SocketIO 세팅
socketio = SocketIO(app, cors_allowed_origins="*")

# 앱 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///secondhand.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key_here'  # JWT 토큰 발급용 키

# 업로드 경로 설정
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# DB, 마이그레이션, JWT 초기화
db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

#--------------여기까지 flask 설정-------------

# 기본 루트
@app.route('/')
def index():
    return "Tiny Secondhand Platform Server is Running!"

# 회원가입 API
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json(force=True)

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({"error": "Missing fields"}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already exists"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)

    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User created successfully"}), 201

# 로그인 API
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(force=True)

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    user = User.query.filter_by(username=username).first()

    if not user or not check_password_hash(user.password, password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(identity=str(user.id))  # identity를 문자열로!
    return jsonify({"access_token": access_token}), 200

# 내 프로필 조회 API
@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "bio": user.bio,
        "balance": user.balance
    }), 200

# 다른 유저 프로필 조회 API
@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_profile(user_id):
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    target_user = User.query.get(user_id)

    if not target_user:
        return jsonify({"error": "User not found"}), 404

    # 일반 유저는 비활성화된 유저를 볼 수 없음
    if not target_user.is_active and not current_user.is_admin:
        return jsonify({"error": "User not found or deactivated"}), 404

    if current_user.is_admin:
        # 관리자는 모든 정보, 비활성 유저 포함 조회 가능
        return jsonify({
            "id": target_user.id,
            "username": target_user.username,
            "email": target_user.email,
            "bio": target_user.bio,
            "balance": target_user.balance
        }), 200
    else:
        # 일반 유저는 username, bio만 볼 수 있음
        return jsonify({
            "username": target_user.username,
            "bio": target_user.bio
        }), 200

# 프로필 소개글 업데이트 API
@app.route('/profile/update', methods=['PATCH'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(force=True)
    bio = data.get('bio')

    if bio is None:
        return jsonify({"error": "Bio is required"}), 400

    user.bio = bio
    db.session.commit()

    return jsonify({"message": "Profile updated"}), 200

#비밀번호 변경 API
@app.route('/profile/password', methods=['PATCH'])
@jwt_required()
def update_password():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json(force=True)
    old_password = data.get('old_password')
    new_password = data.get('new_password')

    if not old_password or not new_password:
        return jsonify({"error": "Both old and new passwords are required"}), 400

    if not check_password_hash(user.password, old_password):
        return jsonify({"error": "Old password is incorrect"}), 400

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"message": "Password updated successfully"}), 200


# 상품 등록 API
@app.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    user_id = get_jwt_identity()
    title = request.form.get('title')
    description = request.form.get('description')
    price = request.form.get('price')

    if not title or not price:
        return jsonify({"error": "Title and price are required"}), 400

    # 상품 먼저 생성
    new_product = Product(
        seller_id=user_id,
        title=title,
        description=description,
        price=price,
        created_at=datetime.utcnow(),
        is_active=True
    )
    db.session.add(new_product)
    db.session.commit()

    # 파일 처리
    images = request.files.getlist('images')
    if len(images) > 5:
        return jsonify({"error": "Maximum 5 images allowed"}), 400

    for image in images:
        if image:
            filename = secure_filename(image.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(save_path)

            product_image = ProductImage(
                product_id=new_product.id,
                image_filename=filename
            )
            db.session.add(product_image)

    db.session.commit()

    return jsonify({"message": "Product created successfully"}), 201

# 전체 상품 목록 조회
@app.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()

    product_list = []
    for product in products:
        product_list.append({
            "id": product.id,
            "seller_id": product.seller_id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": product.is_active
        })

    return jsonify(product_list), 200

# 상품 수정
@app.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    user_id = get_jwt_identity()
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product.seller_id != int(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.get_json(force=True)

    title = data.get('title')
    description = data.get('description')
    price = data.get('price')

    if title:
        product.title = title
    if description:
        product.description = description
    if price:
        product.price = price

    db.session.commit()

    return jsonify({"message": "Product updated successfully"}), 200

# 상품 상세 조회
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    # 해당 상품의 이미지 조회
    images = ProductImage.query.filter_by(product_id=product.id).all()
    image_filenames = [img.image_filename for img in images]

    return jsonify({
        "id": product.id,
        "seller_id": product.seller_id,
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "is_active": product.is_active,
        "images": image_filenames  # 이미지 파일명 리스트 추가
    }), 200

# 파일 다운로드(이미지 제공) API
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# 상품 삭제 API
@app.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    user_id = get_jwt_identity()
    product = Product.query.get(product_id)

    if not product:
        return jsonify({"error": "Product not found"}), 404

    if product.seller_id != int(user_id):
        return jsonify({"error": "Unauthorized"}), 403

    # 연관된 이미지들 가져오기
    images = ProductImage.query.filter_by(product_id=product.id).all()

    for img in images:
        # 실제 파일 삭제
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], img.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
        
        # DB에서 이미지 레코드 삭제
        db.session.delete(img)

    # 상품 삭제
    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product and associated images deleted successfully"}), 200

#상품 검색
@app.route('/products/search', methods=['GET'])
def search_products():
    keyword = request.args.get('keyword', '')

    if not keyword:
        return jsonify({"error": "Keyword is required"}), 400

    products = Product.query.filter(
        (Product.title.ilike(f'%{keyword}%')) | (Product.description.ilike(f'%{keyword}%'))
    ).all()

    product_list = []
    for product in products:
        images = [img.image_filename for img in product.images]

        product_list.append({
            "id": product.id,
            "seller_id": product.seller_id,
            "title": product.title,
            "description": product.description,
            "price": product.price,
            "created_at": product.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "is_active": product.is_active,
            "images": images
        })

    return jsonify(product_list), 200

# 채팅방 생성
@app.route('/chats', methods=['POST'])
@jwt_required()
def create_chat():
    user_id = get_jwt_identity()
    data = request.get_json(force=True)
    target_user_id = data.get('target_user_id')

    if not target_user_id:
        return jsonify({"error": "Target user id is required"}), 400

    if int(user_id) == int(target_user_id):
        return jsonify({"error": "Cannot create chat room with yourself"}), 400

    # 기존에 동일한 방이 있는지 확인
    existing_room = ChatRoom.query.filter(
        ((ChatRoom.user1_id == user_id) & (ChatRoom.user2_id == target_user_id)) |
        ((ChatRoom.user1_id == target_user_id) & (ChatRoom.user2_id == user_id))
    ).first()

    if existing_room:
        return jsonify({"message": "Chat room already exists", "chat_room_id": existing_room.id}), 200

    # 새로운 채팅방 생성
    new_room = ChatRoom(user1_id=user_id, user2_id=target_user_id)
    db.session.add(new_room)
    db.session.commit()

    return jsonify({"message": "Chat room created", "chat_room_id": new_room.id}), 201

# 채팅방 목록 조회 (최신 메시지 기준 정렬)
@app.route('/chats', methods=['GET'])
@jwt_required()
def get_chats():
    user_id = get_jwt_identity()

    rooms = ChatRoom.query.filter(
        (ChatRoom.user1_id == user_id) | (ChatRoom.user2_id == user_id)
    ).all()

    room_list = []
    for room in rooms:
        latest_message = ChatMessage.query.filter_by(room_id=room.id).order_by(ChatMessage.created_at.desc()).first()

        if latest_message:
            latest_message_text = latest_message.message
            latest_message_time = latest_message.created_at.strftime("%Y-%m-%d %H:%M:%S")
        else:
            latest_message_text = None
            latest_message_time = None

        room_list.append({
            "id": room.id,
            "user1_id": room.user1_id,
            "user2_id": room.user2_id,
            "created_at": room.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "latest_message": latest_message_text,
            "latest_message_time": latest_message_time
        })

    # 최신 메시지 시간 기준으로 정렬 (내림차순)
    sorted_rooms = sorted(room_list, key=lambda x: (x['latest_message_time'] is not None, x['latest_message_time']), reverse=True)

    return jsonify(sorted_rooms), 200


# 메시지 보내기
@app.route('/chats/<int:chat_id>/messages', methods=['POST'])
@jwt_required()
def send_message(chat_id):
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True)
    message = data.get('message')

    if not message:
        return jsonify({"error": "Message content is required"}), 400

    # 채팅방 존재 확인
    room = ChatRoom.query.get(chat_id)
    if not room:
        return jsonify({"error": "Chat room not found"}), 404

    if user_id not in [room.user1_id, room.user2_id]:
        return jsonify({"error": "Unauthorized"}), 403

    new_message = ChatMessage(
        room_id=chat_id,
        sender_id=user_id,
        message=message
    )
    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully"}), 201

# 메시지 목록 조회
@app.route('/chats/<int:chat_id>/messages', methods=['GET'])
@jwt_required()
def get_messages(chat_id):
    user_id = int(get_jwt_identity())

    room = ChatRoom.query.get(chat_id)
    if not room:
        return jsonify({"error": "Chat room not found"}), 404

    if user_id not in [room.user1_id, room.user2_id]:
        return jsonify({"error": "Unauthorized"}), 403

    messages = ChatMessage.query.filter_by(room_id=chat_id).order_by(ChatMessage.created_at).all()

    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })

    return jsonify(message_list), 200

# 전체 채팅 메시지 보내기 API
@app.route('/global_chats', methods=['POST'])
@jwt_required()
def send_global_message():
    user_id = get_jwt_identity()
    data = request.get_json(force=True)

    message = data.get('message')
    if not message:
        return jsonify({"error": "Message content required"}), 400

    new_message = GlobalChatMessage(
        sender_id=user_id,
        message=message,
        created_at=datetime.utcnow()
    )

    db.session.add(new_message)
    db.session.commit()

    return jsonify({"message": "Message sent successfully"}), 201

# Socket.IO 이벤트
# 클라이언트 연결
@socketio.on('connect')
def handle_connect():
    print('Client connected')

# 클라이언트 연결 해제
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

# 클라이언트가 메시지를 보낼 때
@socketio.on('send_message')
def handle_send_message(data):
    token = data.get('token')
    message = data.get('message')

    if not token or not message:
        return

    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
        user = User.query.get(user_id)
        if not user:
            return

        username = user.username

        # DB 저장
        new_message = GlobalChatMessage(
            sender_id=user.id,
            username=username,
            message=message,
            created_at=datetime.utcnow()
        )
        db.session.add(new_message)
        db.session.commit()

        # 모든 클라이언트에게 전달
        emit('receive_message', {
            'username': username,
            'message': message
        }, broadcast=True)

    except Exception as e:
        print(f"Token error: {e}")
        return

# 기존 전체 메시지를 반환하는 API
@app.route('/global_chats', methods=['GET'])
def get_global_chats():
    messages = GlobalChatMessage.query.order_by(GlobalChatMessage.created_at.asc()).all()

    message_list = []
    for msg in messages:
        username = msg.username

        message_list.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "username": username,
            "message": msg.message,
            "created_at": msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })
    return jsonify(message_list), 200


# 불량 유저 또는 상품 신고하기
@app.route('/reports', methods=['POST'])
@jwt_required()
def create_report():
    user_id = int(get_jwt_identity())
    data = request.get_json(force=True)

    target_user_id = data.get('target_user_id')
    target_product_id = data.get('target_product_id')
    reason = data.get('reason')

    if not reason:
        return jsonify({"error": "Reason is required"}), 400

    if not target_user_id and not target_product_id:
        return jsonify({"error": "Target user or product must be specified"}), 400

    new_report = Report(
        reporter_id=user_id,
        target_user_id=target_user_id,
        target_product_id=target_product_id,
        reason=reason,
        created_at=datetime.utcnow()
    )

    db.session.add(new_report)
    db.session.commit()

    return jsonify({"message": "Report submitted successfully"}), 201

# 관리자 전용 상품 삭제
@app.route('/admin/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def admin_delete_product(product_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"error": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully by admin"}), 200

# 관리자 전용 유저 비활성화
@app.route('/admin/users/<int:user_id>/deactivate', methods=['PUT'])
@jwt_required()
def admin_deactivate_user(user_id):
    admin_id = int(get_jwt_identity())
    admin = User.query.get(admin_id)

    if not admin or not admin.is_admin:
        return jsonify({"error": "Admin privileges required"}), 403

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not user.is_active:
        return jsonify({"error": "User is already deactivated"}), 400

    user.is_active = False
    db.session.commit()

    return jsonify({"message": "User deactivated successfully"}), 200

# 유저 간 송금
@app.route('/transactions', methods=['POST'])
@jwt_required()
def send_money():
    sender_id = int(get_jwt_identity())
    data = request.get_json(force=True)

    receiver_id = data.get('receiver_id')
    amount = data.get('amount')

    if not receiver_id or not amount:
        return jsonify({"error": "Receiver and amount are required"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    sender = User.query.get(sender_id)
    receiver = User.query.get(receiver_id)

    if not receiver:
        return jsonify({"error": "Receiver not found"}), 404

    if sender.balance < amount:
        return jsonify({"error": "Insufficient balance"}), 400

    sender.balance -= amount
    receiver.balance += amount

    # Transaction 기록 저장
    new_tx = Transaction(
        sender_id=sender_id,
        receiver_id=receiver_id,
        amount=amount,
        created_at=datetime.utcnow()
    )
    db.session.add(new_tx)
    db.session.commit()

    return jsonify({"message": "Transaction completed successfully"}), 200

# 입출금 내역 조회(보낸 것 + 받은 것 전체 조회)
@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    user_id = int(get_jwt_identity())

    sent_transactions = Transaction.query.filter_by(sender_id=user_id).all()
    received_transactions = Transaction.query.filter_by(receiver_id=user_id).all()

    transactions = []

    # 보낸 송금 기록
    for tx in sent_transactions:
        transactions.append({
            "id": tx.id,
            "sender_id": tx.sender_id,
            "receiver_id": tx.receiver_id,
            "amount": tx.amount,
            "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "direction": "sent"
        })

    # 받은 송금 기록
    for tx in received_transactions:
        transactions.append({
            "id": tx.id,
            "sender_id": tx.sender_id,
            "receiver_id": tx.receiver_id,
            "amount": tx.amount,
            "created_at": tx.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "direction": "received"
        })

    # 최신순 정렬
    transactions.sort(key=lambda x: x['created_at'], reverse=True)

    return jsonify(transactions), 200


# 서버 실행
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)