# Python Todo API

Todo API; FastAPI kullanarak yazılmış bir backend projesidir. Veritabanı olarak PostgreSQL, Caching için Redis ve arka plan işlemleri için Celery ve veritabanı iletişimi için SQLAlchemy kullanır.


## Özellikler
* JWT Authorization/Authentication
* Refresh Token
* Account Verify
* Two-Factor Login
* Sending Mail
* Redis Caching
### Mail Açıklamaları
* Yeni bir kullanıcı oluşturulursa, hesabını doğrulaması gerekir. Bunun için oluşturulduğu anda hesabına bir doğrulama bağlantısı gönderilir.
* Kullanıcı İki adımlı doğrulamayı(TFA) açmışsa, login denemesinden sonra mail adresine kod gönderilir. O kodu ilgili endpoint ile girerek giriş sağlayabilir.
* Kullanıcının görevlerinin, tahmini bitiş süresi eğer geçmiş ise (12 saatte bir kontrol edilir) kullanıcıya hatırlatma maili gönderilir.

## Kullanılan Teknolojiler/Kütüphaneler
| Kütüphane   | Açıklama | Kullanım Alanı |
|-------------|----------|----------------|
| **FastAPI** | Modern, hızlı (high-performance) web framework | RESTful API servisleri oluşturmak, Güvenlik kontrolü |
| **Celery**  | Asenkron görev kuyruğu sistemi | Arka plan görevleri ve zamanlanmış işler çalıştırmak |
| **SQLAlchemy** | SQL - ORM Aracı | Uygulama veritabanı yapılandırılması ve iletişimi |
| **Redis**   | Bellek içi veri yapısı ve mesaj kuyruğu | Celery broker & result backend olarak, blacklist jti, deleted user, TFA Kod kontrolü |
| **python-jose** | JWT token oluşturma ve doğrulama | Kullanıcı kimlik doğrulama (Auth) işlemleri |
| **smtplib** | Yerleşik e-posta gönderimi | Mail gönderimi (hesap doğrulama, iki aşamalı giriş, süresi geçen task bildirimi vb.) |

## Endpoint Bilgileri

| **Kategori**         | **Yöntem** | **Endpoint**                        | **Açıklama**                        |
|----------------------|------------|-------------------------------------|-------------------------------------|
| **Authorization/Authentication** | POST       | `/auth/tfa/login`                   | TFA ile giriş yapma                |
|                      | POST       | `/auth/refresh`                     | Refresh token alma                  |
|                      | GET        | `/auth/tfa/exp`                     | TFA süresinin bitişini al          |
|                      | GET        | `/auth/verify/{token}`              | Hesap doğrulaması                   |
| **User**              | POST       | `/user/login`                       | Kullanıcı giriş yapma              |
|                      | POST       | `/user/logout`                      | Kullanıcı çıkışı                    |
|                      | POST       | `/user/info/`                       | Kullanıcı bilgisi al               |
|                      | POST       | `/user/create/`                     | Kullanıcı oluşturma                 |
|                      | PATCH      | `/user/update/`                     | Kullanıcı bilgisi güncelleme        |
|                      | POST       | `/user/delete/`                     | Kullanıcı silme                     |
| **Priority**          | GET        | `/priority/get/{priority_id}/`      | Öncelik bilgisi al                 |
|                      | GET        | `/priority/list/`                   | Öncelik listesi al                 |
|                      | POST       | `/priority/create/`                 | Öncelik oluşturma                   |
|                      | PATCH      | `/priority/update/{priority_id}/`   | Öncelik güncelleme                  |
|                      | DELETE     | `/priority/delete/{priority_id}/`   | Öncelik silme                       |
| **Status**            | GET        | `/status/get/{status_id}/`          | Durum bilgisi al                   |
|                      | GET        | `/status/list/`                     | Durum listesi al                   |
|                      | POST       | `/status/create/`                   | Durum oluşturma                     |
|                      | PATCH      | `/status/update/{status_id}/`       | Durum güncelleme                    |
|                      | DELETE     | `/status/delete/{status_id}/`       | Durum silme                         |
| **Task**              | GET        | `/task/get/{task_id}/`              | Görev bilgisi al                   |
|                      | GET        | `/task/list/`                       | Görev listesi al                   |
|                      | POST       | `/task/create/`                     | Görev oluşturma                     |
|                      | PATCH      | `/task/update/{task_id}/`           | Görev güncelleme                    |
|                      | DELETE     | `/task/delete/{task_id}/`           | Görev silme                         |

### **Açıklamalar**:
1. **Authorization/Authentication**: Kullanıcıların giriş yapabilmesi, doğrulama, ve refresh token gibi işlemler burada yapılır.
2. **User**: Kullanıcı işlemleri (giriş, çıkış, bilgileri alma, oluşturma, güncelleme, silme) bu uç noktalarda yapılır.
3. **Priority**: Görev önceliği ile ilgili işlemler (oluşturma, güncelleme, listeleme, silme) yapılır.
4. **Status**: Görevlerin durumu ile ilgili işlemler (oluşturma, güncelleme, listeleme, silme) yapılır.
5. **Task**: Görevler ile ilgili işlemler (oluşturma, güncelleme, listeleme, silme) yapılır.

Yeni bir kullanıcı oluşturulduğunda o kullanıcıya varsayılan olarak; "Done" Statusu ve "High" Priority kayıdı atanır.
Burada ilk oluşturulan Status, atandığı Task durumunun bittiğini bildirir.
* Varsayılan statusun yalnızca adı değiştirilebilir.

Login işlemlerinde; `/user/login/` endpoint'ine istek eğer TFA ile yapılırsa `{'login_type': 'two_factor'}` dönecek, maile kod gönderilecektir ve `tfa_token` çerezi oluşturulacaktır.

Bundan sonra `/auth/tfa/login` endpointine belirtilmiş olan body bilgisi ve tfa çerezi ile birlikte istek atıldığında, doğrulama işleminden geçtikten sonra, giriş sağlanıp; access token ve refresh token verilecektir.
Kullanıcı oluşturma isteği hariç her istekte Authorization Header bildirilmelidir. Detaylı kullanım için;

[![Video](/readme_imgs/video.PNG)](https://streamable.com/0cfzfw)

## Kurulum
Eğer `uv` kullanıyorsanız:

* `cd TodoApi`
* `uv venv .venv`
* Windows: `.venv\Scripts\Activate`
* MacOS/Linux: `source .venv\bin\activate`
* `uv sync --all-extras`

Eğer `pip` kullanıyorsanız:

* `cd TodoApi`
* `python -m virtualenv .venv`
* Windows: `.venv\Scripts\Activate`
* MacOS/Linux: `source .venv\bin\activate`
*  `pip install -r requirements.txt`

## TodoAPI Çalıştırma
Environment(.env) dosyadaki configürasyonları tamamlayın. Redis ve PostgreSQL uygulamalarınızın aktif olduğundan emin olun.
* `cd TodoApi`
### FastAPI
* `python -m uvicorn apps.main:app --reload`

### Celery Worker
* `python -m celery -A apps.celery_app.app worker -c 2 --loglevel=info --pool=gevent`

### Celery Beat
* `python -m celery -A apps.celery_app.app beat --loglevel=info`

## Lisans
Bu proje [MIT Lisansı](./LICENSE) ile lisanslanmıştır.

