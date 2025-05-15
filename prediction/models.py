from django.db import models
from django.contrib.auth import get_user_model
from core.utils.helpers import get_file_path
import uuid

User = get_user_model()

class PatientCaseRepository:
    """
    Hasta vakaları için MongoDB repository sınıfı
    Django ORM yerine doğrudan MongoDB koleksiyonları üzerinde çalışır
    """
    
    COLLECTION_NAME = 'patient_cases'
    
    def __init__(self, db):
        self.collection = db[self.COLLECTION_NAME]
    
    def create(self, data):
        """Yeni vaka oluştur"""
        # UUID ekle
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid4())
            
        # Oluşturma tarihi ekle
        if 'created_at' not in data:
            from django.utils import timezone
            data['created_at'] = timezone.now()
            
        # Varsayılan durum
        if 'status' not in data:
            data['status'] = 'pending'
            
        # Veriyi kaydet
        result = self.collection.insert_one(data)
        
        # Kaydedilen dokümanı döndür
        return self.get_by_id(result.inserted_id)
    
    def get_by_id(self, case_id):
        """ID'ye göre vaka getir"""
        from bson import ObjectId
        if isinstance(case_id, str):
            case_id = ObjectId(case_id)
            
        return self.collection.find_one({'_id': case_id})
    
    def get_by_uuid(self, uuid):
        """UUID'ye göre vaka getir"""
        return self.collection.find_one({'uuid': uuid})
    
    def get_by_doctor(self, doctor_id):
        """Doktor ID'sine göre vakaları getir"""
        return list(self.collection.find({'doctor_id': str(doctor_id)}))
    
    def update(self, case_id, data):
        """Vakayı güncelle"""
        from bson import ObjectId
        if isinstance(case_id, str):
            case_id = ObjectId(case_id)
            
        # Güncelleme tarihi ekle
        if 'updated_at' not in data:
            from django.utils import timezone
            data['updated_at'] = timezone.now()
            
        result = self.collection.update_one(
            {'_id': case_id},
            {'$set': data}
        )
        
        return result.modified_count > 0
    
    def delete(self, case_id):
        """Vakayı sil"""
        from bson import ObjectId
        if isinstance(case_id, str):
            case_id = ObjectId(case_id)
            
        result = self.collection.delete_one({'_id': case_id})
        
        return result.deleted_count > 0

class ImageSampleRepository:
    """
    Görüntü örnekleri için MongoDB repository sınıfı
    Django ORM yerine doğrudan MongoDB koleksiyonları üzerinde çalışır
    """
    
    COLLECTION_NAME = 'image_samples'
    
    def __init__(self, db):
        self.collection = db[self.COLLECTION_NAME]
    
    def create(self, data):
        """Yeni görüntü örneği oluştur"""
        # UUID ekle
        if 'uuid' not in data:
            data['uuid'] = str(uuid.uuid4())
            
        # Yükleme tarihi ekle
        if 'uploaded_at' not in data:
            from django.utils import timezone
            data['uploaded_at'] = timezone.now()
            
        # Boş tahminler dizisi
        if 'predictions' not in data:
            data['predictions'] = []
            
        # Veriyi kaydet
        result = self.collection.insert_one(data)
        
        # Kaydedilen dokümanı döndür
        return self.get_by_id(result.inserted_id)
    
    def get_by_id(self, image_id):
        """ID'ye göre görüntü getir"""
        from bson import ObjectId
        if isinstance(image_id, str):
            image_id = ObjectId(image_id)
            
        return self.collection.find_one({'_id': image_id})
    
    def get_by_uuid(self, uuid):
        """UUID'ye göre görüntü getir"""
        return self.collection.find_one({'uuid': uuid})
    
    def get_by_case(self, case_id):
        """Vaka ID'sine göre görüntüleri getir"""
        return list(self.collection.find({'case_id': str(case_id)}))
    
    def add_prediction(self, image_id, prediction_data):
        """Görüntüye tahmin ekle"""
        from bson import ObjectId
        if isinstance(image_id, str):
            image_id = ObjectId(image_id)
            
        # Tahmin oluşturma tarihi ekle
        if 'created_at' not in prediction_data:
            from django.utils import timezone
            prediction_data['created_at'] = timezone.now()
            
        result = self.collection.update_one(
            {'_id': image_id},
            {'$push': {'predictions': prediction_data}}
        )
        
        return result.modified_count > 0
    
    def update(self, image_id, data):
        """Görüntüyü güncelle"""
        from bson import ObjectId
        if isinstance(image_id, str):
            image_id = ObjectId(image_id)
        
        # Güncelleme tarihi ekle
        if 'updated_at' not in data:
            from django.utils import timezone
            data['updated_at'] = timezone.now()
            
        # 'predictions' alanını doğrudan güncellemeyi engelle
        if 'predictions' in data:
            del data['predictions']
            
        result = self.collection.update_one(
            {'_id': image_id},
            {'$set': data}
        )
        
        return result.modified_count > 0
    
    def delete(self, image_id):
        """Görüntüyü sil"""
        from bson import ObjectId
        if isinstance(image_id, str):
            image_id = ObjectId(image_id)
            
        result = self.collection.delete_one({'_id': image_id})
        
        return result.deleted_count > 0