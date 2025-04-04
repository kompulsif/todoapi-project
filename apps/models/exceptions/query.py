class BaseActionException(Exception):
    """
    Hatalarda kullanilacak base model
    """

    def __init__(self, message):
        self.message = message
        super().__init__(self, message)


class PriorityNotFound(BaseActionException):
    """Kullanilmak istenen oncelik degeri yoksa yukseltilir"""


class PriorityValidateException(BaseActionException):
    """Kullanilmak uzere gelen veri gecerli olmadiginda yukseltilir"""


class StatusNotFound(BaseActionException):
    """Kullanilmak istenen statu degeri yoksa yukseltilir"""


class DefaultStatusFound(BaseActionException):
    """Varsayilan status silinmeye calisilirsa yukseltilir"""


class StatusValidateException(BaseActionException):
    """Kullanilmak uzere gelen veri gecerli olmadiginda yukseltilir"""


class TaskValidateException(BaseActionException):
    """Kullanicidan gelen veri gecerli olmadiginda yukseltilir"""


class TaskNotFound(BaseActionException):
    """Istenilen gorev bulunamazsa yukseltilir"""


class TaskUpdateFailed(BaseActionException):
    """Gorevn guncelleme islemlerinde kullanilacak hata"""


class TaskCreateFailed(BaseActionException):
    """Gorev olusturma islemlerinde kullanilacak hata"""


class TaskDeleteFailed(BaseActionException):
    """Gorev silme islemlerinde kullanilacak hata"""


class UserNotFound(BaseActionException):
    """Istenilen kullanici bulunamazsa yukseltilir"""


class UserUpdateFailed(BaseActionException):
    """Kullanici guncelleme islemlerinde kullanilacak hata"""


class UserCreateFailed(BaseActionException):
    """Kullanici olusturma islemlerinde kullanilacak hata"""


class UserDeleteFailed(BaseActionException):
    """Kullanici silme islemlerinde kullanilacak hata"""


class UserValidateException(BaseActionException):
    """Kulllanilmak uzere gelen veri gecerli olmadiginda yukseltilir"""
