"""
LungVision AI projesi için özel istisna sınıfları
Bu modül, uygulamanın çeşitli bileşenlerinde kullanılabilecek özel hata türlerini tanımlar.
"""


class LungVisionException(Exception):
    """
    LungVision için temel istisna sınıfı.
    Diğer tüm özel istisnalar bundan türetilir.
    """
    def __init__(self, message="LungVision AI sistemi bir hatayla karşılaştı", code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)


class DatabaseConnectionError(LungVisionException):
    """
    MongoDB veritabanı bağlantısında hata oluştuğunda fırlatılır.
    """
    def __init__(self, message="MongoDB veritabanına bağlanırken hata oluştu", code="db_connection_error"):
        super().__init__(message, code)


class ModelLoadError(LungVisionException):
    """
    TensorFlow modeli yüklenirken hata oluştuğunda fırlatılır.
    """
    def __init__(self, message="Yapay zeka modeli yüklenirken hata oluştu", code="model_load_error"):
        super().__init__(message, code)


class PredictionError(LungVisionException):
    """
    Tahmin işlemi sırasında hata oluştuğunda fırlatılır.
    """
    def __init__(self, message="Tahmin işlemi sırasında bir hata oluştu", code="prediction_error"):
        super().__init__(message, code)


class GradCAMGenerationError(LungVisionException):
    """
    Grad-CAM görselleştirmesi oluşturulurken hata oluştuğunda fırlatılır.
    """
    def __init__(self, message="Grad-CAM görselleştirmesi oluşturulurken hata oluştu", code="gradcam_generation_error"):
        super().__init__(message, code)


class InvalidFileFormatError(LungVisionException):
    """
    Geçersiz dosya formatı yüklendiğinde fırlatılır.
    """
    def __init__(self, message="Desteklenmeyen dosya formatı", code="invalid_file_format"):
        super().__init__(message, code)


class ResourceNotFoundError(LungVisionException):
    """
    Talep edilen kaynak bulunamadığında fırlatılır.
    """
    def __init__(self, message="Talep edilen kaynak bulunamadı", code="resource_not_found"):
        super().__init__(message, code)


class PermissionDeniedError(LungVisionException):
    """
    Kullanıcı bir kaynağa erişim iznine sahip olmadığında fırlatılır.
    """
    def __init__(self, message="Bu işlemi gerçekleştirmek için yetkiniz yok", code="permission_denied"):
        super().__init__(message, code)