import datetime
import pymongo
from bson import ObjectId
from django.utils import timezone
from core.db import MongoManager

class AnalyticsService:
    """
    Dashboard için analitik ve istatistik hesaplama servisi
    """
    def __init__(self):
        self.mongo = MongoManager()
        self.db = self.mongo.db
        
        # Tahmin sınıfları ve renk kodları
        self.prediction_classes = {
            'lung_aca': {
                'display_name': 'Akciğer Adenokarsinomu',
                'color': '#FF6384'
            },
            'lung_scc': {
                'display_name': 'Akciğer Skuamöz Hücreli Karsinomu',
                'color': '#36A2EB'
            },
            'lung_n': {
                'display_name': 'Normal Akciğer Dokusu',
                'color': '#4BC0C0'
            }
        }
    
    def get_prediction_distribution(self, doctor_id=None):
        """
        Tahmin dağılımını hesaplar
        Args:
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
        Returns:
            List: Sınıflara göre tahmin dağılımı
        """
        if self.db is None:
            return []
        
        # MongoDB pipeline
        pipeline = [
            # Görüntü koleksiyonundan tahminleri ayrıştır
            {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
            # Tahmin sınıflarına göre grupla
            {"$group": {
                "_id": "$predictions.predicted_class",
                "count": {"$sum": 1}
            }},
            # Sonuçları sırala
            {"$sort": {"count": -1}}
        ]
        
        # Doktor filtresi ekle
        if doctor_id:
            # Önce vakaları doktora göre filtrele
            cases = list(self.db.patient_cases.find({"doctor_id": str(doctor_id)}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Sonra görüntüleri bu vakalara göre filtrele
            pipeline.insert(0, {"$match": {"case_id": {"$in": case_ids}}})
        
        # Pipeline'ı çalıştır
        results = list(self.db.image_samples.aggregate(pipeline))
        
        # Toplam tahmin sayısını hesapla
        total_predictions = sum(item["count"] for item in results)
        
        # Sonuçları formatlayıp renk ve görüntü isimlerini ekle
        formatted_results = []
        for item in results:
            class_name = item["_id"]
            count = item["count"]
            percentage = (count / total_predictions) * 100 if total_predictions > 0 else 0
            
            class_info = self.prediction_classes.get(class_name, {
                'display_name': class_name,
                'color': '#FFCE56'  # Bilinmeyen sınıflar için varsayılan renk
            })
            
            formatted_results.append({
                'class_name': class_name,
                'count': count,
                'percentage': percentage,
                'display_name': class_info['display_name'],
                'color': class_info['color']
            })
        
        return formatted_results
    
    def get_recent_activity(self, limit=10, user_id=None):
        """
        Son aktiviteleri döndürür (yeni vakalar ve tahminler)
        Args:
            limit: Sonuç sayısı limiti
            user_id: Belirli bir kullanıcının verilerini filtrelemek için ID
        Returns:
            List: Son aktiviteler
        """
        if self.db is None:
            return []
        
        activities = []
        
        # Yeni vakalar
        case_query = {}
        if user_id:
            case_query["doctor_id"] = str(user_id)
        
        recent_cases = list(self.db.patient_cases.find(
            case_query,
            {"uuid": 1, "patient_id": 1, "doctor_name": 1, "created_at": 1}
        ).sort("created_at", pymongo.DESCENDING).limit(limit))
        
        for case in recent_cases:
            activities.append({
                'type': 'new_case',
                'patient_id': case.get('patient_id', ''),
                'doctor_name': case.get('doctor_name', ''),
                'timestamp': case.get('created_at', datetime.datetime.now()),
                'case_uuid': case.get('uuid', '')
            })
        
        # Yeni tahminler
        # İlk önce görüntüleri ve tahminleri al
        pipeline = [
            {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
            {"$sort": {"predictions.created_at": -1}},
            {"$limit": limit}
        ]
        
        # Doktor filtresi ekle
        if user_id:
            # Önce vakaları doktora göre filtrele
            cases = list(self.db.patient_cases.find({"doctor_id": str(user_id)}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Sonra görüntüleri bu vakalara göre filtrele
            pipeline.insert(0, {"$match": {"case_id": {"$in": case_ids}}})
        
        recent_predictions = list(self.db.image_samples.aggregate(pipeline))
        
        for pred in recent_predictions:
            # Vaka bilgilerini al
            case = self.db.patient_cases.find_one({"_id": ObjectId(pred.get('case_id', ''))})
            
            activities.append({
                'type': 'new_prediction',
                'patient_id': case.get('patient_id', '') if case else '',
                'doctor_name': case.get('doctor_name', '') if case else '',
                'timestamp': pred.get('predictions', {}).get('created_at', datetime.datetime.now()),
                'case_uuid': case.get('uuid', '') if case else '',
                'predicted_class': pred.get('predictions', {}).get('predicted_class', ''),
                'confidence': pred.get('predictions', {}).get('confidence', 0)
            })
        
        # Zamanlamaya göre sırala
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Limiti uygula
        return activities[:limit]
    
    def get_cases_summary(self, doctor_id=None):
        """
        Vakaların özet bilgilerini döndürür
        Args:
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
        Returns:
            List: Vaka özetleri
        """
        if self.db is None:
            return []
        
        # Vaka sorgusu
        case_query = {}
        if doctor_id:
            case_query["doctor_id"] = str(doctor_id)
        
        # Vakaları al
        cases = list(self.db.patient_cases.find(case_query).sort("created_at", pymongo.DESCENDING))
        
        summaries = []
        for case in cases:
            case_id = case['_id']
            
            # Bu vakaya ait görüntü sayısını bul
            image_count = self.db.image_samples.count_documents({"case_id": str(case_id)})
            
            # Bu vakaya ait tahmin sayısını bul
            pipeline = [
                {"$match": {"case_id": str(case_id)}},
                {"$project": {"prediction_count": {"$size": {"$ifNull": ["$predictions", []]}}}},
                {"$group": {"_id": None, "total": {"$sum": "$prediction_count"}}}
            ]
            prediction_count_result = list(self.db.image_samples.aggregate(pipeline))
            prediction_count = prediction_count_result[0]['total'] if prediction_count_result else 0
            
            # Son tahmini bul
            last_prediction = None
            if prediction_count > 0:
                pipeline = [
                    {"$match": {"case_id": str(case_id)}},
                    {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
                    {"$sort": {"predictions.created_at": -1}},
                    {"$limit": 1},
                    {"$project": {"prediction": "$predictions"}}
                ]
                last_prediction_result = list(self.db.image_samples.aggregate(pipeline))
                last_prediction = last_prediction_result[0]['prediction'] if last_prediction_result else None
            
            # Özet bilgileri ekle
            summary = {
                'id': str(case_id),
                'uuid': case.get('uuid', ''),
                'patient_id': case.get('patient_id', ''),
                'status': case.get('status', ''),
                'created_at': case.get('created_at', datetime.datetime.now()),
                'doctor_name': case.get('doctor_name', ''),
                'image_count': image_count,
                'prediction_count': prediction_count
            }
            
            if last_prediction:
                summary['last_prediction'] = last_prediction
            
            summaries.append(summary)
        
        return summaries
    
    def get_case_distribution_by_status(self, doctor_id=None):
        """
        Durumlara göre vaka dağılımını döndürür
        Args:
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
        Returns:
            List: Durumlara göre vaka dağılımı
        """
        if self.db is None:
            return []
        
        # Pipeline
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        # Doktor filtresi ekle
        if doctor_id:
            pipeline.insert(0, {"$match": {"doctor_id": str(doctor_id)}})
        
        # Pipeline'ı çalıştır
        results = list(self.db.patient_cases.aggregate(pipeline))
        
        # Durumları ve renkleri tanımla
        status_colors = {
            'pending': '#FFD700',    # Sarı
            'in_progress': '#1E90FF', # Mavi
            'completed': '#32CD32',   # Yeşil
            'archived': '#A9A9A9'     # Gri
        }
        
        status_display = {
            'pending': 'Beklemede',
            'in_progress': 'İşlemde',
            'completed': 'Tamamlandı',
            'archived': 'Arşivlendi'
        }
        
        # Toplam vaka sayısını hesapla
        total_cases = sum(item["count"] for item in results)
        
        # Sonuçları formatlayıp renk ve görüntü isimlerini ekle
        formatted_results = []
        for item in results:
            status = item["_id"]
            count = item["count"]
            percentage = (count / total_cases) * 100 if total_cases > 0 else 0
            
            formatted_results.append({
                'status': status,
                'display_name': status_display.get(status, status),
                'count': count,
                'percentage': percentage,
                'color': status_colors.get(status, '#CCCCCC')  # Bilinmeyen durumlar için varsayılan renk
            })
        
        return formatted_results
    
    def get_prediction_timeline(self, days=30, doctor_id=None):
        """
        Zaman içinde tahmin dağılımını döndürür
        Args:
            days: Gün sayısı
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
        Returns:
            Dict: Zaman serisi verileri
        """
        if self.db is None:
            return {'dates': [], 'series': []}
        
        # Başlangıç ve bitiş tarihlerini hesapla
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Pipeline
        pipeline = [
            {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
            {"$match": {"predictions.created_at": {"$gte": start_date, "$lte": end_date}}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$predictions.created_at"}},
                    "class": "$predictions.predicted_class"
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.date": 1}}
        ]
        
        # Doktor filtresi ekle
        if doctor_id:
            # Önce vakaları doktora göre filtrele
            cases = list(self.db.patient_cases.find({"doctor_id": str(doctor_id)}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Sonra görüntüleri bu vakalara göre filtrele
            pipeline.insert(0, {"$match": {"case_id": {"$in": case_ids}}})
        
        # Pipeline'ı çalıştır
        results = list(self.db.image_samples.aggregate(pipeline))
        
        # Tarih listesi oluştur
        date_list = []
        current_date = start_date
        while current_date <= end_date:
            date_list.append(current_date.strftime('%Y-%m-%d'))
            current_date += datetime.timedelta(days=1)
        
        # Sınıf bazında seri verileri hazırla
        series_data = {}
        for cls in self.prediction_classes.keys():
            series_data[cls] = {date: 0 for date in date_list}
        
        # Sonuçları seriye ekle
        for item in results:
            date = item['_id']['date']
            cls = item['_id']['class']
            count = item['count']
            
            if cls in series_data and date in series_data[cls]:
                series_data[cls][date] = count
        
        # Görselleştirme için seri verilerini düzenle
        series = []
        for cls, values in series_data.items():
            cls_info = self.prediction_classes.get(cls, {
                'display_name': cls,
                'color': '#FFCE56'
            })
            
            series.append({
                'name': cls_info['display_name'],
                'data': list(values.values()),
                'color': cls_info['color']
            })
        
        return {
            'dates': date_list,
            'series': series
        }
    
    def get_prediction_confidence_distribution(self, doctor_id=None):
        """
        Tahmin güven düzeyi dağılımını döndürür
        Args:
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
        Returns:
            Dict: Güven düzeyi aralıklarına göre dağılım
        """
        if self.db is None:
            return {'ranges': [], 'counts': [], 'classes': {}}
        
        # Güven düzeyi aralıkları
        confidence_ranges = [
            (0.0, 0.2),
            (0.2, 0.4),
            (0.4, 0.6),
            (0.6, 0.8),
            (0.8, 1.0)
        ]
        
        # Pipeline
        pipeline = [
            {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
        ]
        
        # Doktor filtresi ekle
        if doctor_id:
            # Önce vakaları doktora göre filtrele
            cases = list(self.db.patient_cases.find({"doctor_id": str(doctor_id)}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Sonra görüntüleri bu vakalara göre filtrele
            pipeline.insert(0, {"$match": {"case_id": {"$in": case_ids}}})
        
        # Pipeline'ı çalıştır
        results = list(self.db.image_samples.aggregate(pipeline))
        
        # Sonuçları aralıklara göre grupla
        range_counts = {f"{r[0]:.1f}-{r[1]:.1f}": 0 for r in confidence_ranges}
        class_range_counts = {}
        
        for item in results:
            prediction = item.get('predictions', {})
            confidence = prediction.get('confidence', 0)
            pred_class = prediction.get('predicted_class', '')
            
            # Aralık kontrolü
            for r_min, r_max in confidence_ranges:
                if r_min <= confidence < r_max:
                    range_key = f"{r_min:.1f}-{r_max:.1f}"
                    range_counts[range_key] += 1
                    
                    # Sınıf bazlı istatistik
                    if pred_class not in class_range_counts:
                        class_range_counts[pred_class] = {f"{r[0]:.1f}-{r[1]:.1f}": 0 for r in confidence_ranges}
                    
                    class_range_counts[pred_class][range_key] += 1
                    break
        
        # Sınıf serilerini hazırla
        class_series = {}
        for cls, counts in class_range_counts.items():
            cls_info = self.prediction_classes.get(cls, {
                'display_name': cls,
                'color': '#FFCE56'
            })
            
            class_series[cls] = {
                'name': cls_info['display_name'],
                'data': list(counts.values()),
                'color': cls_info['color']
            }
        
        return {
            'ranges': list(range_counts.keys()),
            'counts': list(range_counts.values()),
            'classes': class_series
        }
    
    def get_doctor_activity(self):
        """
        Doktor aktivitesini döndürür
        Returns:
            List: Doktor bazında aktivite verileri
        """
        if self.db is None:
            return []
        
        # Doktor başına vaka sayısını al
        case_pipeline = [
            {"$group": {
                "_id": "$doctor_id",
                "doctor_name": {"$first": "$doctor_name"},
                "case_count": {"$sum": 1}
            }}
        ]
        
        case_results = list(self.db.patient_cases.aggregate(case_pipeline))
        
        # Doktor ve vaka ID'lerini eşleştir
        doctor_cases = {}
        for item in case_results:
            doctor_id = item['_id']
            doctor_cases[doctor_id] = {
                'doctor_name': item['doctor_name'],
                'case_count': item['case_count'],
                'prediction_count': 0,
                'last_activity': None
            }
        
        # Doktor başına tahmin sayısını al
        # Önce her doktorun vakalarını bul
        for doctor_id in doctor_cases.keys():
            cases = list(self.db.patient_cases.find({"doctor_id": doctor_id}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Bu vakalara ait tahmin sayısını bul
            if case_ids:
                pipeline = [
                    {"$match": {"case_id": {"$in": case_ids}}},
                    {"$unwind": {"path": "$predictions", "preserveNullAndEmptyArrays": False}},
                    {"$group": {
                        "_id": None,
                        "prediction_count": {"$sum": 1},
                        "last_activity": {"$max": "$predictions.created_at"}
                    }}
                ]
                
                pred_results = list(self.db.image_samples.aggregate(pipeline))
                
                if pred_results:
                    doctor_cases[doctor_id]['prediction_count'] = pred_results[0].get('prediction_count', 0)
                    doctor_cases[doctor_id]['last_activity'] = pred_results[0].get('last_activity')
        
        # Sonuçları düzenle
        activity_data = []
        for doctor_id, data in doctor_cases.items():
            activity_data.append({
                'doctor_id': doctor_id,
                'doctor_name': data['doctor_name'],
                'case_count': data['case_count'],
                'prediction_count': data['prediction_count'],
                'last_activity': data['last_activity']
            })
        
        # Son aktiviteye göre sırala
        activity_data.sort(key=lambda x: x['last_activity'] if x['last_activity'] else datetime.datetime.min, reverse=True)
        
        return activity_data