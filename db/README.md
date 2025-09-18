# Database
## DB파일 초기에 작성한 버전부터 최근까지 작성한 MySQL&SQLite용 쿼리문 + VisualStudio 콘솔용 코드
유저정보, 퀴즈 진행도, 비밀번호 초기화/재설정 기능에 필요한 인증코드 등의 저장용 DB 작성 및 이메일 인증을 위한 연결용 코드
파일 형식은 .txt파일

## 대부분의 코드는 MySQL에서 사용할 목적으로 작성한 코드
SQLite는 DB 전체코드로 1개 있는데 MySQL쿼리의 일부분만 변경하면 SQLite에서 바로 사용할 수 있고 DB에 저장되는 정보가 MySQL에 저장될 정보 안에 SQLite에 저장할 정보가 포함되어 있기 때문

## 코드 설명 
users 테이블
유저의 정보 저장용 테이블

### 설명 :

user_no : 사용자에게 임의로 할당된 고유번호

user_id : 사용자의 id = 닉네임

username : 사용자의 실명

password : 사용자가 설정한 비밀번호 / salt : 비밀번호의 암호화를 위한 무작위 데이터

email : 사용자가 사용하는 이메일

phone_number : 사용자의 전화번호 / birth_date : 사용자의 생년월일 / grade : 사용자의 학년 / major : 사용자의 학과

created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP : 사용자가 가입한 시간을 저장하기 위한 코드

    CREATE TABLE IF NOT EXISTS users (
                        user_no INT UNSIGNED NOT NULL UNIQUE AUTO_INCREMENT,
                        user_id VARCHAR(50) PRIMARY KEY,
                        username VARCHAR(50) NOT NULL,
                        password VARCHAR(255) NOT NULL,
                        salt VARCHAR(255) NOT NULL,
                        email VARCHAR(100) NOT NULL UNIQUE,
                        phone_number VARCHAR(20),
                        birth_date DATE,
                        grade VARCHAR(20),
                        major VARCHAR(50),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );

quiz_log 테이블

### 설명 :  

퀴즈 풀이 기록용

log_id : 기록에 임의로 할당하는 id

quiz_id : 각각의 퀴즈에 임의로 부여된 id

is_correct BOOLEAN NOT NULL : 퀴즈의 t/f 저장

answered_at DATETIME DEFAULT CURRENT_TIMESTAMP : 퀴즈를 언제 풀었는지 자동적으로 저장

user_id와 quiz_id는 외래 키로 지정하여 다른 테이블에서 참조함

    CREATE TABLE IF NOT EXISTS quiz_log (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id VARCHAR(50) NOT NULL, 
    quiz_id INT UNSIGNED NOT NULL,
    is_correct BOOLEAN NOT NULL,
    answered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quiz(quiz_id) ON DELETE CASCADE);

비밀번호 암호화 코드

### 설명 :

HashPassword 메소드 : 비밀번호를 처음으로 암호화(해싱)하는 기능

|_ byte[] saltBytes = new byte[16]; : 비밀번호에 추가할 16바이트 크기의 무작위 데이터 저장공간 생

   rng.GetBytes(saltBytes); : 난수 생성 후 저장

   new Rfc2898DeriveBytes(... :  PBKDF2 알고리즘을 사용하여 해시를 생성

   saltBytes: 위에서 생성한 고유한 솔트

   100000: 반복 횟수. 해싱 과정을 10만 번 반복하여 계산 시간을 의도적으로 늘림으로 무차별 대입 공격(Brute-force attack)을 어렵게 만듦

   HashAlgorithmName.SHA256: 해싱 내부에서 사용할 알고리즘으로 SHA-256을 지정

   pbkdf2.GetBytes(32): 최종적으로 32바이트(256비트) 길이의 해시 값을 생성

   Convert.ToBase64String(... : 생성된 salt와 hash는 이진(binary) 데이터이므로, 데이터베이스에 텍스트 형태로 쉽게 저장하기 위해 Base64 문자열로 변환하여 반환

VerifyPassword 메소드 : 비밀번호 검증 기능

   byte[] saltBytes = Convert.FromBase64String(storedSalt); 해싱 과정과 똑같은 파라미터를 사용해 해시를 다시 생성: 데이터베이스에 저장되어 있던 사용자의 Base64 salt 문자열을 다시 이진 데이터로 변환
   
   new Rfc2898DeriveBytes(... : 해싱 과정과 똑같은 파라미터를 사용해 해시를 다시 생성

   Convert.ToBase64String(hash) == storedHash;: 새로 생성된 해시와 데이터베이스에 저장되어 있던 storedHash를 비교 / 일치하면 true(로그인 성공), 불일치하면 false(로그인 실패)를 반환

    public static class PasswordHasher
        {
            public static string HashPassword(string password, out string salt)
            {
                byte[] saltBytes = new byte[16];
                using (var rng = RandomNumberGenerator.Create())
                {
                    rng.GetBytes(saltBytes);
                }
                salt = Convert.ToBase64String(saltBytes);
                using (var pbkdf2 = new Rfc2898DeriveBytes(password, saltBytes, 100000, HashAlgorithmName.SHA256))
                {
                    byte[] hash = pbkdf2.GetBytes(32);
                    return Convert.ToBase64String(hash);
                }
            }

            public static bool VerifyPassword(string password, string storedHash, string storedSalt)
            {
                byte[] saltBytes = Convert.FromBase64String(storedSalt);
                using (var pbkdf2 = new Rfc2898DeriveBytes(password, saltBytes, 100000, HashAlgorithmName.SHA256))
                {
                    byte[] hash = pbkdf2.GetBytes(32);
                    return Convert.ToBase64String(hash) == storedHash;
                }
            }

   솔트(salt)값을 사용하는 이유 : 동일한 비밀번호(예: '1234')를 사용하는 여러 사용자가 있더라도, 각자 다른 솔트 값을 가지므로 데이터베이스에 저장되는 최종 해시 값은 모두 달라지게 되는데 이를 통해 레인보우 테이블 공격을 효과적으로 방지할 수 있음

   왜 100,000번이나 반복하는지 : 해싱에 일부러 시간을 소요시켜, 공격자가 초당 수십억 개의 비밀번호를 대입해보는 무차별 대입 공격의 속도를 현저히 늦춤으로 최대한 비밀번호의 특정을 늦출 수 있음
