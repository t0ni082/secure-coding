# 1. 회원가입 (Register)
http POST http://127.0.0.1:5000/register username="testuser" email="test@example.com" password="1234"
http POST http://127.0.0.1:5000/register username="user2" email="user2@example.com" password="1234"
http POST http://127.0.0.1:5000/register username="user3" email="user3@example.com" password="1234"

# 2. 로그인 (Login)
http POST http://127.0.0.1:5000/login username="testuser" password="1234"
# => 받은 access_token 저장

http POST http://127.0.0.1:5000/login username="user2" password="1234"
# => 받은 access_token 저장

# 3. 프로필 조회 (Profile)
http GET http://127.0.0.1:5000/profile "Authorization: Bearer <access_token>"

# 4. 상품 등록 (Create Product)
http POST http://127.0.0.1:5000/products "Authorization: Bearer <access_token>" title="화이트하임" description="아주 맛있는 화이트하임" price:=3333
http POST http://127.0.0.1:5000/products "Authorization: Bearer <access_token>" title="블랙하임" description="아주 맛없는 블랙하임" price:=6666

# 5. 전체 상품 목록 조회 (List Products)
http GET http://127.0.0.1:5000/products

# 6. 상품 상세 조회 (Product Detail)
http GET http://127.0.0.1:5000/products/1

# 7. 상품 수정 (Update Product)
http PUT http://127.0.0.1:5000/products/1 "Authorization: Bearer <access_token>" title="화이트하임 (수정)" price:=4000

# 8. 상품 삭제 (Delete Product)
http DELETE http://127.0.0.1:5000/products/1 "Authorization: Bearer <access_token>"

# 9. 상품 검색 (Search Products)
http GET http://127.0.0.1:5000/products/search keyword=="화이트하임"

# 10. 채팅방 생성 (Create Chat Room)
http POST http://127.0.0.1:5000/chats "Authorization: Bearer <access_token>" target_user_id:=2

# 11. 내 채팅방 목록 조회 (List My Chat Rooms)
http GET http://127.0.0.1:5000/chats "Authorization: Bearer <access_token>"

# 12. 채팅 메시지 보내기 (Send Chat Message)
http POST http://127.0.0.1:5000/chats/1/messages "Authorization: Bearer <access_token>" message="Welcome! user2!"

# 13. 채팅 메시지 목록 조회 (List Chat Messages)
http GET http://127.0.0.1:5000/chats/1/messages "Authorization: Bearer <access_token>"

# 14. 상품 신고하기 (Report)
http POST http://127.0.0.1:5000/reports "Authorization: Bearer <access_token>" target_product_id:=2 reason="맛이 없음. 나쁜 블랙하임."

# 15. 관리자 - 상품 삭제 (Admin Delete Product)
http DELETE http://127.0.0.1:5000/admin/products/2 "Authorization: Bearer <admin_access_token>"

# 16. 관리자 - 유저 비활성화 (Admin Deactivate User)
http DELETE http://127.0.0.1:5000/admin/users/2 "Authorization: Bearer <admin_access_token>"

# 17. 송금 (Send Money)
http POST http://127.0.0.1:5000/transactions "Authorization: Bearer <access_token>" receiver_id:=2 amount:=1000
http POST http://127.0.0.1:5000/transactions "Authorization: Bearer <access_token>" receiver_id:=1 amount:=500

# 18. 송금 내역 조회 (View Transactions)
http GET http://127.0.0.1:5000/transactions "Authorization: Bearer <access_token>"

# 19. 마이페이지 프로필 소개
http PATCH http://127.0.0.1:5000/profile/update "Authorization: Bearer <access_token>" bio="중고거래 사이트 관리자(문의: 1대1 채팅으로)"

# 20. 프로필 비밀번호 변경
http PATCH http://127.0.0.1:5000/profile/password "Authorization: Bearer <access_token>" old_password="1234" new_password="0000" 

# 21. 다른 유저 조회 기능(관리자 입장에서 & 일반 유저 입장에서. 둘 다 check!)
http GET http://127.0.0.1:5000/users/(번호) "Authorization: Bearer <access_token>" 
# 21-1. 다른 유저 정보 추가.
http PATCH http://127.0.0.1:5000/profile/update "Authorization: Bearer <user2의_토큰>" bio="안녕하세요! 저는 user2입니다."
#21-2. 다른 유저 잔액 변경(관리자 모드)
flask shell

from models import db, User
user = User.query.filter_by(username="user2").first()
user.balance = (원하는 금액)
db.session.commit()

exit() 혹은 quit()

# 22. 실시간 전체 채팅
http POST http://127.0.0.1:5000/global_chats "Authorization: Bearer <access_token>" message="관리자 테스트 메세지입니다."
# user2로 채팅 전송
http POST http://127.0.0.1:5000/login username="user2" password="1234"
http POST http://127.0.0.1:5000/global_chats "Authorization: Bearer {user2_access_token}" message="user2 테스트 메시지입니다."

# 23. 전체 채팅 내역 조회(누구의 토큰이든 상관 없음)
http GET http://127.0.0.1:5000/global_chats "Authorization: Bearer {access_token}"

# 24. 채팅방 최신 메세지 조회
http POST http://127.0.0.1:5000/chats/1/messages "Authorization: Bearer <토큰>" message="최신 메시지 테스트"
# 채팅방 목록 조회
http GET http://127.0.0.1:5000/chats "Authorization: Bearer <토큰>"

# 25. 채팅 최신 내역 불러오기
http POST http://127.0.0.1:5000/chats/1/messages "Authorization: Bearer <본인 access_token>" message="테스트 메시지 1" 
http GET http://127.0.0.1:5000/chats "Authorization: Bearer <본인 access_token>" 


# 26. 상품 이미지 등록(최대 5개)
http --form POST http://127.0.0.1:5000/products "Authorization: Bearer <토큰>" title="FC서울 유니폼 세트" description="FC서울 홈/어웨이/골키퍼 유니폼 세트입니다." price="160000" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_1.png" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_2.png" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_3.png" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_4.png" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_5.png"
#전체 상품 조회
http GET http://127.0.0.1:5000/products
#특정 상품 조회
http GET http://127.0.0.1:5000/products/(상품 순서)


# 27. 상품 상세 조회(이미지도 나오도록!)
http GET http://127.0.0.1:5000/products/(상품 순서)

# 28. 상품 대표 이미지 출력되도록!
# 예시 1) "유니폼" 키워드로 상품 검색
http GET http://127.0.0.1:5000/products/search keyword=="유니폼"
# 예시 2) "화이트" 키워드로 상품 검색
http GET http://127.0.0.1:5000/products/search keyword=="화이트"


# 29. 상품 삭제 시(이미지도 삭제 되도록)
http --form POST http://127.0.0.1:5000/products "Authorization: Bearer <토큰>" title="FC서울 유니폼 (테스트)" description="삭제 테스트용입니다." price="100000" images@"C:\Users\anton\Pictures\secondhand_image\fc seoul uniform_6.png" 
http DELETE http://127.0.0.1:5000/products/3 "Authorization: Bearer <토큰>"
