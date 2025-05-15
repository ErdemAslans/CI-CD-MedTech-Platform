import json
import os
import datetime
from datetime import datetime
import tempfile
from django.conf import settings
from django.template.loader import render_to_string
from core.db import MongoManager
from .analytics_service import AnalyticsService

class ReportService:
    """
    Dashboard raporları oluşturma servisi
    """
    def __init__(self):
        self.mongo = MongoManager()
        self.analytics = AnalyticsService()
    
    def generate_case_report(self, case_id, format='json'):
        """
        Belirli bir vaka için rapor oluşturur
        Args:
            case_id: Vaka ID'si
            format: Rapor formatı (json, pdf, csv)
        Returns:
            str: Rapor dosyası yolu veya JSON veri
        """
        if self.mongo.db is None:
            return None
        
        # Vakayı al
        case = self.mongo.db.patient_cases.find_one({"_id": case_id})
        if not case:
            return None
        
        # Vakaya ait görüntüleri al
        images = list(self.mongo.db.image_samples.find({"case_id": str(case_id)}))
        
        # Tarih alanını formatla
        created_at_str = "N/A"
        if 'created_at' in case and case['created_at']:
            try:
                # Eğer zaten datetime ise
                if isinstance(case['created_at'], datetime):
                    created_at_str = case['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                # Eğer string ise tarih formatına dönüştür
                elif isinstance(case['created_at'], str):
                    try:
                        # ISO format deneme
                        created_at = datetime.fromisoformat(case['created_at'].replace('Z', '+00:00'))
                        created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        # Diğer format denemeleri
                        try:
                            created_at = datetime.strptime(case['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            created_at_str = str(case.get('created_at'))
            except Exception as e:
                # Herhangi bir hata durumunda string olarak bırak
                created_at_str = str(case.get('created_at'))
        
        # Case ID'yi de include et
        case_id_str = str(case.get('_id'))
        
        # Vaka ve tahmin verilerini hazırla
        report_data = {
            'case': {
                'id': case_id_str,  # Burada case_id'yi ekleyin
                'uuid': case.get('uuid'),
                'patient_id': case.get('patient_id'),
                'status': case.get('status'),
                'doctor_name': case.get('doctor_name'),
                'created_at': created_at_str,
                'notes': case.get('notes', ''),
                'patient_info': case.get('patient_info', {})
            },
            'images': [],
            'predictions': []
        }
        
        # Görüntü ve tahmin verilerini ekle
        for img in images:
            # Görüntü yükleme tarihini formatla
            uploaded_at_str = "N/A"
            if 'uploaded_at' in img and img['uploaded_at']:
                try:
                    # Eğer zaten datetime ise
                    if isinstance(img['uploaded_at'], datetime):
                        uploaded_at_str = img['uploaded_at'].strftime('%Y-%m-%d %H:%M:%S')
                    # Eğer string ise tarih formatına dönüştür
                    elif isinstance(img['uploaded_at'], str):
                        try:
                            # ISO format deneme
                            uploaded_at = datetime.fromisoformat(img['uploaded_at'].replace('Z', '+00:00'))
                            uploaded_at_str = uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            # Diğer format denemeleri
                            try:
                                uploaded_at = datetime.strptime(img['uploaded_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                                uploaded_at_str = uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                uploaded_at_str = str(img['uploaded_at'])
                except Exception as e:
                    # Herhangi bir hata durumunda string olarak bırak
                    uploaded_at_str = str(img.get('uploaded_at'))
            
            image_data = {
                'id': str(img.get('_id')),
                'uuid': img.get('uuid'),
                'description': img.get('description', ''),
                'uploaded_at': uploaded_at_str,
                'uploaded_by': img.get('uploaded_by_name', ''),
                'image_path': img.get('image_path', '')
            }
            
            report_data['images'].append(image_data)
            
            # Tahminleri ekle
            predictions = img.get('predictions', [])
            for pred in predictions:
                # Tahmin tarihini formatla
                pred_created_at_str = "N/A"
                if 'created_at' in pred and pred['created_at']:
                    try:
                        # Eğer zaten datetime ise
                        if isinstance(pred['created_at'], datetime):
                            pred_created_at_str = pred['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                        # Eğer string ise tarih formatına dönüştür
                        elif isinstance(pred['created_at'], str):
                            try:
                                # ISO format deneme
                                pred_created_at = datetime.fromisoformat(pred['created_at'].replace('Z', '+00:00'))
                                pred_created_at_str = pred_created_at.strftime('%Y-%m-%d %H:%M:%S')
                            except ValueError:
                                # Diğer format denemeleri
                                try:
                                    pred_created_at = datetime.strptime(pred['created_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                                    pred_created_at_str = pred_created_at.strftime('%Y-%m-%d %H:%M:%S')
                                except ValueError:
                                    pred_created_at_str = str(pred['created_at'])
                    except Exception as e:
                        # Herhangi bir hata durumunda string olarak bırak
                        pred_created_at_str = str(pred.get('created_at'))
                
                pred_data = {
                    'image_id': str(img.get('_id')),
                    'image_uuid': img.get('uuid'),
                    'predicted_class': pred.get('predicted_class', ''),
                    'predicted_class_display': pred.get('predicted_class_display', ''),
                    'confidence': pred.get('confidence', 0),
                    'probabilities': pred.get('probabilities', {}),
                    'created_at': pred_created_at_str,
                    'model_version': pred.get('model_version', ''),
                    'processing_time': pred.get('processing_time', 0),
                    'gradcam_path': pred.get('gradcam_path', '')
                }
                
                report_data['predictions'].append(pred_data)
        
        # Format bazlı çıktı
        if format == 'json':
            return report_data
        elif format == 'pdf':
            # PDF raporunu oluştur
            return self._generate_pdf_report(report_data)
        elif format == 'csv':
            # CSV raporunu oluştur
            return self._generate_csv_report(report_data)
        else:
            return report_data
    
    def generate_dashboard_report(self, doctor_id=None, days=30, format='json'):
        """
        Dashboard verileri için özet rapor oluşturur
        Args:
            doctor_id: Belirli bir doktorun verilerini filtrelemek için ID
            days: Gün sayısı
            format: Rapor formatı (json, pdf, csv)
        Returns:
            str: Rapor dosyası yolu veya JSON veri
        """
        if self.mongo.db is None:
            return None
        
        # Analitik verilerini al
        prediction_distribution = self.analytics.get_prediction_distribution(doctor_id=doctor_id)
        case_distribution = self.analytics.get_case_distribution_by_status(doctor_id=doctor_id)
        prediction_timeline = self.analytics.get_prediction_timeline(days=days, doctor_id=doctor_id)
        confidence_distribution = self.analytics.get_prediction_confidence_distribution(doctor_id=doctor_id)
        
        # Vaka sayılarını hesapla
        case_query = {}
        if doctor_id:
            case_query["doctor_id"] = str(doctor_id)
        
        total_cases = self.mongo.db.patient_cases.count_documents(case_query)
        
        # Tahmin sayısını hesapla
        pipeline = [
            {"$project": {"prediction_count": {"$size": {"$ifNull": ["$predictions", []]}}}}
        ]
        
        if doctor_id:
            # Önce vakaları doktora göre filtrele
            cases = list(self.mongo.db.patient_cases.find({"doctor_id": str(doctor_id)}, {"_id": 1}))
            case_ids = [str(case["_id"]) for case in cases]
            
            # Sonra görüntüleri bu vakalara göre filtrele
            if case_ids:
                pipeline.insert(0, {"$match": {"case_id": {"$in": case_ids}}})
            else:
                # Eğer doktorun vakası yoksa, tahmin de yoktur
                total_predictions = 0
                pipeline = []
        
        if pipeline:
            result = list(self.mongo.db.image_samples.aggregate(pipeline))
            total_predictions = sum(doc.get('prediction_count', 0) for doc in result)
        else:
            total_predictions = 0
        
        # Şu anki zamanı string olarak formatla
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Rapor verilerini hazırla
        report_data = {
            'timestamp': current_time_str,
            'period': f"Son {days} gün",
            'total_cases': total_cases,
            'total_predictions': total_predictions,
            'prediction_distribution': prediction_distribution,
            'case_distribution': case_distribution,
            'prediction_timeline': prediction_timeline,
            'confidence_distribution': confidence_distribution
        }
        
        # Format bazlı çıktı
        if format == 'json':
            return report_data
        elif format == 'pdf':
            # PDF raporunu oluştur
            return self._generate_pdf_report(report_data, template='dashboard/report.html')
        elif format == 'csv':
            # CSV raporunu oluştur
            return self._generate_csv_report(report_data)
        else:
            return report_data
    
    def _generate_pdf_report(self, data, template='cases/report.html'):
        """
        PDF raporu oluşturur
        Args:
            data: Rapor verileri
            template: Kullanılacak şablon adı
        Returns:
            str: PDF dosyası yolu
        """
        # Bu kısım gerçek bir PDF oluşturucu kütüphane gerektirir
        # Örnek olarak HTML şablonunu render edelim
        html_content = render_to_string(template, {'data': data})
        
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as temp:
            temp.write(html_content.encode('utf-8'))
            temp_path = temp.name
        
        # Gerçek bir uygulamada, Weasyprint veya wkhtmltopdf ile PDF oluşturulur
        # Bu örnek için sadece HTML dosyası döndürelim
        return temp_path
    
    def _generate_csv_report(self, data):
        """
        CSV raporu oluşturur
        Args:
            data: Rapor verileri
        Returns:
            str: CSV dosyası yolu
        """
        # CSV içeriğini oluştur
        csv_content = "timestamp,field,value\n"
        
        # Şu anki zamanı string olarak formatla
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Basit değerleri ekle
        for key, value in data.items():
            if not isinstance(value, (list, dict)):
                csv_content += f"{current_time_str},{key},{value}\n"
        
        # Geçici dosya oluştur
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
            temp.write(csv_content.encode('utf-8'))
            temp_path = temp.name
        
        return temp_path