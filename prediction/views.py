from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from core.db import MongoManager
from bson import ObjectId
import os
import cv2
from django.conf import settings
from ml.predictor import LungCancerPredictor
from datetime import datetime

# Yetki kontrol dekoratörü
def doctor_or_pathologist_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not hasattr(request.user, 'user_type') or request.user.user_type not in ['doctor', 'pathologist', 'admin']:
            return redirect('core:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@login_required
@doctor_or_pathologist_required
def case_list(request):
    """Hasta vakalarını listele"""
    mongo = MongoManager()
    
    # Doktora özel vaka filtresi
    query = {}
    if request.user.user_type not in ['admin']:
        query['doctor_id'] = str(request.user.id)
    
    # Durum filtresi
    status_filter = request.GET.get('status')
    if status_filter:
        query['status'] = status_filter
    
    # Vakaları al
    cases = list(mongo.db.patient_cases.find(query).sort('created_at', -1))
    
    # ObjectId'leri string'e dönüştür
    for case in cases:
        case['id'] = str(case['_id'])
        del case['_id']
    
    return render(request, 'cases/list.html', {
        'cases': cases,
        'status_filter': status_filter
    })

@login_required
@doctor_or_pathologist_required
def case_create(request):
    """Yeni vaka oluşturma formu ve işlemi"""
    if request.method == 'POST':
        # API serializer'ı kullanmak yerine, daha basit bir form işleme yapılabilir
        patient_id = request.POST.get('patient_id')
        notes = request.POST.get('notes', '')
        status = request.POST.get('status', 'pending')
        
        if not patient_id:
            return render(request, 'cases/form.html', {
                'error': 'Hasta ID gereklidir.'
            })
        
        # MongoDB'ye kaydet
        from prediction.models import PatientCaseRepository
        mongo = MongoManager()
        case_repo = PatientCaseRepository(mongo.db)
        
        case_data = {
            'patient_id': patient_id,
            'notes': notes,
            'status': status,
            'doctor_id': str(request.user.id),
            'doctor_name': request.user.get_full_name()
        }
        
        new_case = case_repo.create(case_data)
        if new_case:
            return redirect('prediction:case_detail', case_id=str(new_case['_id']))
        else:
            return render(request, 'cases/form.html', {
                'error': 'Vaka oluşturulurken bir hata oluştu.'
            })
    
    return render(request, 'cases/form.html')

@login_required
@doctor_or_pathologist_required
def case_detail(request, case_id):
    """Vaka detaylarını gösterme"""
    mongo = MongoManager()
    
    # Vaka var mı kontrol et
    try:
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
    except:
        return redirect('prediction:case_list')
    
    if not case:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    if request.user.user_type not in ['admin'] and str(case.get('doctor_id')) != str(request.user.id):
        return redirect('prediction:case_list')
    
    # _id'yi id olarak ayarla
    case['id'] = str(case['_id'])
    del case['_id']
    
    # Vakaya ait görüntüleri al
    images = list(mongo.db.image_samples.find({'case_id': case_id}).sort('uploaded_at', -1))
    
    for image in images:
        image['id'] = str(image['_id'])
        del image['_id']
        
        # Son tahmini al
        if 'predictions' in image and image['predictions']:
            image['last_prediction'] = image['predictions'][-1]
    
    return render(request, 'cases/detail.html', {
        'case': case,
        'images': images
    })

@login_required
@doctor_or_pathologist_required
def case_edit(request, case_id):
    """Vaka düzenleme formu ve işlemi"""
    mongo = MongoManager()
    
    # Vaka var mı kontrol et
    try:
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
    except:
        return redirect('prediction:case_list')
    
    if not case:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    if request.user.user_type not in ['admin'] and str(case.get('doctor_id')) != str(request.user.id):
        return redirect('prediction:case_list')
    
    # _id'yi id olarak ayarla
    case['id'] = str(case['_id'])
    
    if request.method == 'POST':
        # Form verilerini al
        patient_id = request.POST.get('patient_id')
        notes = request.POST.get('notes', '')
        status = request.POST.get('status')
        
        if not patient_id:
            return render(request, 'cases/form.html', {
                'case': case,
                'error': 'Hasta ID gereklidir.'
            })
        
        # MongoDB'de güncelle
        from prediction.models import PatientCaseRepository
        case_repo = PatientCaseRepository(mongo.db)
        
        update_data = {
            'patient_id': patient_id,
            'notes': notes,
            'status': status
        }
        
        success = case_repo.update(case_id, update_data)
        
        if success:
            return redirect('prediction:case_detail', case_id=case_id)
        else:
            return render(request, 'cases/form.html', {
                'case': case,
                'error': 'Vaka güncellenirken bir hata oluştu.'
            })
    
    return render(request, 'cases/form.html', {'case': case})

@login_required
@doctor_or_pathologist_required
def case_delete(request, case_id):
    """Vaka silme işlemi"""
    # Sadece admin silebilir
    if request.user.user_type not in ['admin']:
        return redirect('prediction:case_list')
    
    mongo = MongoManager()
    
    # Vaka var mı kontrol et
    try:
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
    except:
        return redirect('prediction:case_list')
    
    if not case:
        return redirect('prediction:case_list')
    
    if request.method == 'POST':
        # MongoDB'den sil
        from prediction.models import PatientCaseRepository
        case_repo = PatientCaseRepository(mongo.db)
        
        success = case_repo.delete(case_id)
        
        if success:
            # Vakaya ait görüntüleri de sil
            mongo.db.image_samples.delete_many({'case_id': case_id})
            
            return redirect('prediction:case_list')
        else:
            return render(request, 'cases/confirm_delete.html', {
                'case': case,
                'error': 'Vaka silinirken bir hata oluştu.'
            })
    
    # _id'yi id olarak ayarla
    case['id'] = str(case['_id'])
    
    return render(request, 'cases/confirm_delete.html', {'case': case})

@login_required
@doctor_or_pathologist_required
def image_list(request, case_id):
    """Bir vakaya ait görüntüleri listele"""
    mongo = MongoManager()
    
    # Vaka var mı kontrol et
    try:
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
    except:
        return redirect('prediction:case_list')
    
    if not case:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    if request.user.user_type not in ['admin'] and str(case.get('doctor_id')) != str(request.user.id):
        return redirect('prediction:case_list')
    
    # _id'yi id olarak ayarla
    case['id'] = str(case['_id'])
    
    # Vakaya ait görüntüleri al
    images = list(mongo.db.image_samples.find({'case_id': case_id}).sort('uploaded_at', -1))
    
    for image in images:
        image['id'] = str(image['_id'])
        del image['_id']
        
        # Son tahmini al
        if 'predictions' in image and image['predictions']:
            image['last_prediction'] = image['predictions'][-1]
    
    return render(request, 'cases/image_list.html', {
        'case': case,
        'images': images
    })

@login_required
@doctor_or_pathologist_required
def image_upload(request, case_id=None):
    """Görüntü yükleme işlemi - AJAX desteği ile"""
    import logging
    logger = logging.getLogger('django')
    logger.debug("image_upload view called with case_id: %s", case_id)
    
    mongo = MongoManager()
    
    # AJAX isteği mi kontrol et
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
   
    # Vaka var mı kontrol et (sadece case_id verilmişse)
    if case_id:
        try:
            case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
            if not case:
                if is_ajax:
                    return JsonResponse({"status": "error", "message": "Vaka bulunamadı"}, status=404)
                return redirect('prediction:case_list')
            
            # Yetki kontrolü
            if request.user.user_type not in ['admin'] and str(case.get('doctor_id')) != str(request.user.id):
                if is_ajax:
                    return JsonResponse({"status": "error", "message": "Bu vakaya erişim izniniz yok"}, status=403)
                return redirect('prediction:case_list')
                
            # _id'yi id olarak ayarla
            case['id'] = str(case['_id'])
        except Exception as e:
            logger.error(f"Case lookup error: {str(e)}")
            if is_ajax:
                return JsonResponse({"status": "error", "message": f"Vaka arama hatası: {str(e)}"}, status=400)
            return redirect('prediction:case_list')
    else:
        case = None
   
    if request.method == 'POST':
        logger.debug("POST request received")
        description = request.POST.get('description', '')
        case_id = request.POST.get('case_id', case_id)  # Form'dan gelen vaka ID'si veya URL'deki
        image_file = request.FILES.get('image')
        
        logger.debug("image_file present: %s", image_file is not None)
        logger.debug("case_id from form or URL: %s", case_id)
       
        if not image_file:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Görüntü dosyası gereklidir"}, status=400)
            return render(request, 'prediction/upload.html', {
                'case': case,
                'error': 'Görüntü dosyası gereklidir.'
            })
            
        if not case_id:
            if is_ajax:
                return JsonResponse({"status": "error", "message": "Vaka ID gereklidir"}, status=400)
            return render(request, 'prediction/upload.html', {
                'case': case,
                'error': 'Vaka ID gereklidir.'
            })
       
        try:
            # Doğru import yolunu kullan
            from prediction.services.storage_service import StorageService
            rel_path = StorageService.save_histopathology_image(image_file)
            
            logger.debug("File saved with StorageService at path: %s", rel_path)
            
            # MongoDB'ye kaydet
            from prediction.models import ImageSampleRepository
            image_repo = ImageSampleRepository(mongo.db)
            
            image_data = {
                'case_id': case_id,
                'description': description,
                'image_path': rel_path,
                'uploaded_by': str(request.user.id),
                'uploaded_by_name': request.user.get_full_name(),
                'uploaded_at': datetime.now().isoformat()
            }
            
            logger.debug("Saving to MongoDB with data: %s", image_data)
           
            new_image = image_repo.create(image_data)
           
            if new_image:
                logger.debug("Successfully saved to MongoDB")
                
                if is_ajax:
                    return JsonResponse({
                        "status": "success",
                        "message": "Görüntü başarıyla yüklendi",
                        "image_id": str(new_image['_id']),
                        "image_url": f"{settings.MEDIA_URL}{rel_path}"
                    })
                    
                return redirect('prediction:image_detail', image_id=str(new_image['_id']))
            else:
                logger.error("Failed to save to MongoDB")
                if is_ajax:
                    return JsonResponse({
                        "status": "error",
                        "message": "Görüntü veritabanına kaydedilemedi"
                    }, status=500)
                    
                return render(request, 'prediction/upload.html', {
                    'case': case,
                    'error': 'Görüntü veritabanına kaydedilemedi.'
                })
        except Exception as e:
            logger.exception("Exception while uploading image: %s", str(e))
            
            if is_ajax:
                return JsonResponse({
                    "status": "error",
                    "message": f"Görüntü yükleme hatası: {str(e)}"
                }, status=500)
                
            return render(request, 'prediction/upload.html', {
                'case': case,
                'error': f'Görüntü yükleme hatası: {str(e)}'
            })
   
    # GET isteği için form sayfasını göster
    return render(request, 'prediction/upload.html', {'case': case})

@login_required
@doctor_or_pathologist_required
def image_detail(request, image_id):
    """Görüntü detaylarını gösterme"""
    mongo = MongoManager()
    
    # Görüntü var mı kontrol et
    try:
        image = mongo.db.image_samples.find_one({'_id': ObjectId(image_id)})
    except:
        return redirect('prediction:case_list')
    
    if not image:
        return redirect('prediction:case_list')
    
    # Vaka bilgilerini al
    case_id = image.get('case_id', '')
    case = None
    
    if case_id:
        try:
            case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
        except:
            pass
    
    # _id'yi id olarak ayarla
    image['id'] = str(image['_id'])
    del image['_id']
    
    if case:
        case['id'] = str(case['_id'])
        del case['_id']
    
    # Tahminleri al
    predictions = image.get('predictions', [])
    
    return render(request, 'prediction/detail.html', {
        'image': image,
        'case': case,
        'predictions': predictions
    })

@login_required
@doctor_or_pathologist_required
def case_report(request, case_id):
    """Vaka raporu oluşturma ve görüntüleme"""
    mongo = MongoManager()
    
    # Vaka var mı kontrol et
    try:
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
    except:
        return redirect('prediction:case_list')
    
    if not case:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    if request.user.user_type not in ['admin'] and str(case.get('doctor_id')) != str(request.user.id):
        return redirect('prediction:case_list')
    
    # _id'yi id olarak ayarla
    case_id_str = str(case.get('_id'))
    case['id'] = case_id_str
    
    # Rapor formatı
    format = request.GET.get('format', 'html')
    
    # Rapor servisini kullan
    from dashboard.services.report_service import ReportService
    report_service = ReportService()
    
    # HTML formatı için rapor oluşturma
    if format == 'html':
        report_data = report_service.generate_case_report(ObjectId(case_id), format='json')
        return render(request, 'cases/report.html', {
            'case': case,
            'report': report_data
        })
    elif format == 'pdf':
        # PDF raporu için direkt dosya döndürüyoruz, şablona değişken göndermeye gerek yok
        report_file = report_service.generate_pdf_report_direct(ObjectId(case_id), case)
        from django.http import FileResponse
        return FileResponse(open(report_file, 'rb'), filename=f"case_report_{case_id}.pdf")
    elif format == 'csv':
        # CSV dosyasını indir
        report_file = report_service.generate_case_report(ObjectId(case_id), format='csv')
        from django.http import FileResponse
        return FileResponse(open(report_file, 'rb'), filename=f"case_report_{case_id}.csv")
    else:
        # Diğer formatlar için JSON döndür
        report_data = report_service.generate_case_report(ObjectId(case_id), format='json')
        return render(request, 'cases/report.html', {
            'case': case,
            'report': report_data
        })
# TAHMİN GÖRÜNÜM FONKSİYONLARI (prediction:app_name)

@login_required
@doctor_or_pathologist_required
def prediction_home(request):
    """Tahmin ana sayfası - Yeni vaka oluşturmaya yönlendir"""
    # Kullanıcıyı doğrudan yeni vaka oluşturma sayfasına yönlendir
    return redirect('prediction:case_create')

"""
Düzeltilmiş ve optimize edilmiş görüntü analiz API'si.

Bu fonksiyon, LungCancerPredictor modelini kullanarak histopatolojik görüntü analizi yapar
ve sonuçları JsonResponse olarak döndürür.
"""

@login_required
@doctor_or_pathologist_required
def analyze_image(request, image_id):
    """Görüntü analizi API endpoint'i - AJAX için"""
    import logging
    logger = logging.getLogger('django')
    
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Sadece POST metodu destekleniyor"}, status=405)
    
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_ajax:
        return JsonResponse({"status": "error", "message": "Sadece AJAX istekleri destekleniyor"}, status=400)
    
    mongo = MongoManager()
    
    # Görüntü var mı kontrol et
    try:
        image = mongo.db.image_samples.find_one({'_id': ObjectId(image_id)})
        if not image:
            return JsonResponse({"status": "error", "message": "Görüntü bulunamadı"}, status=404)
    except Exception as e:
        logger.error(f"Görüntü arama hatası: {str(e)}")
        return JsonResponse({"status": "error", "message": f"Görüntü arama hatası: {str(e)}"}, status=400)
    
    # Görüntü yolunu al
    image_path = image.get('image_path')
    if not image_path:
        return JsonResponse({"status": "error", "message": "Görüntü dosya yolu bulunamadı"}, status=404)
    
    # Tam dosya yolu
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)
    if not os.path.exists(full_path):
        return JsonResponse({"status": "error", "message": "Görüntü dosyası disk üzerinde bulunamadı"}, status=404)
    
    try:
        # Görüntüyü yükle
        img = cv2.imread(full_path)
        if img is None:
            return JsonResponse({"status": "error", "message": f"Görüntü yüklenemedi: {full_path}"}, status=500)
        
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Model yükle ve tahmin yap
        from ml.predictor import LungCancerPredictor
        
        try:
            predictor = LungCancerPredictor()
            logger.debug("LungCancerPredictor başarıyla oluşturuldu")
        except Exception as model_error:
            logger.error(f"Model yükleme hatası: {str(model_error)}")
            return JsonResponse({"status": "error", "message": f"Model yükleme hatası: {str(model_error)}"}, status=500)
        
        try:
            prediction_result = predictor.predict(img)
            logger.debug(f"Tahmin sonucu: {prediction_result}")
        except Exception as pred_error:
            logger.error(f"Tahmin hatası: {str(pred_error)}")
            return JsonResponse({"status": "error", "message": f"Tahmin hatası: {str(pred_error)}"}, status=500)
        
        # Grad-CAM oluştur
        gradcam_path = None
        try:
            # Grad-CAM dizinini kontrol et
            gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam')
            if not os.path.exists(gradcam_dir):
                os.makedirs(gradcam_dir, exist_ok=True)
            
            # Grad-CAM görüntüsü oluştur
            cam_image = predictor.get_gradcam(img)
            
            if cam_image is not None:
                # Dosya adını oluştur
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                gradcam_filename = f"gradcam_{image_id}_{timestamp}.jpg"
                gradcam_rel_path = f"gradcam/{gradcam_filename}"
                gradcam_abs_path = os.path.join(settings.MEDIA_ROOT, gradcam_rel_path)
                
                # Kaydet
                success = cv2.imwrite(gradcam_abs_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
                
                # Dosya oluştu mu kontrol et
                if os.path.exists(gradcam_abs_path):
                    gradcam_path = gradcam_rel_path
                    logger.debug(f"Grad-CAM başarıyla kaydedildi: {gradcam_rel_path}")
                else:
                    logger.warning(f"Grad-CAM dosyası oluşturulamadı: {gradcam_abs_path}")
            else:
                logger.warning("Grad-CAM oluşturulamadı: Metot None değer döndürdü")
                    
        except Exception as grad_error:
            # Grad-CAM başarısız olursa devam et ama loglama yap
            logger.error(f"Grad-CAM oluşturulamadı: {str(grad_error)}")
        
        # Tahmin sonucunu güncelle
        prediction_result['gradcam_path'] = gradcam_path
        prediction_result['prediction_time'] = datetime.now().strftime('%d.%m.%Y %H:%M')
        
        # MongoDB'ye kaydet
        try:
            from prediction.models import ImageSampleRepository
            image_repo = ImageSampleRepository(mongo.db)
            success = image_repo.add_prediction(image_id, prediction_result)
            
            if not success:
                logger.error("Tahmin sonucu veritabanına kaydedilemedi")
                return JsonResponse({
                    "status": "error",
                    "message": "Tahmin sonucu veritabanına kaydedilemedi"
                }, status=500)
        except Exception as db_error:
            logger.error(f"Veritabanı kayıt hatası: {str(db_error)}")
            return JsonResponse({
                "status": "error",
                "message": f"Veritabanı kayıt hatası: {str(db_error)}"
            }, status=500)
        
        # Başarılı cevap
        return JsonResponse({
            "status": "success",
            "message": "Tahmin başarıyla tamamlandı",
            "predicted_class": prediction_result['predicted_class'],
            "predicted_class_display": prediction_result['predicted_class_display'],
            "confidence": prediction_result['confidence'] * 100,  # Yüzdelik olarak
            "gradcam_url": f"{settings.MEDIA_URL}{gradcam_path}" if gradcam_path else None,
            "probabilities": prediction_result['probabilities'],
            "prediction_time": prediction_result['prediction_time']
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Analiz işlemi başarısız: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({
            "status": "error",
            "message": f"Analiz işlemi başarısız: {str(e)}"
        }, status=500)

@login_required
@doctor_or_pathologist_required
def predict_image(request, image_id):
    """Görüntü tahmini için sayfa ve işlem"""
    import logging
    logger = logging.getLogger('django')
    
    mongo = MongoManager()
    
    # Görüntü var mı kontrol et
    try:
        image = mongo.db.image_samples.find_one({'_id': ObjectId(image_id)})
    except Exception as e:
        logger.error(f"Görüntü arama hatası: {str(e)}")
        return redirect('prediction:case_list')
        
    if not image:
        logger.warning(f"Görüntü bulunamadı: {image_id}")
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    case_id = image.get('case_id')
    if request.user.user_type not in ['admin'] and case_id:
        try:
            case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
            if case and str(case.get('doctor_id')) != str(request.user.id):
                logger.warning(f"Kullanıcının görüntüye erişim yetkisi yok: {request.user.id}, {image_id}")
                return redirect('prediction:case_list')
        except Exception as e:
            logger.error(f"Vaka arama hatası: {str(e)}")
    
    # _id'yi id olarak ayarla
    image['id'] = str(image['_id'])
    
    # POST isteği ise tahmin başlat
    if request.method == 'POST':
        # AJAX isteği ise asenkron işle
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            logger.debug(f"AJAX tahmin isteği alındı: {image_id}")
            try:
                # Direkt analyze_image fonksiyonunu çağır
                return analyze_image(request, image_id)
            except Exception as e:
                logger.error(f"AJAX tahmin hatası: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                return JsonResponse({
                    "status": "error",
                    "detail": f"Tahmin işlemi başarısız: {str(e)}"
                }, status=500)
        
        # Normal form gönderimi için
        logger.debug(f"Form tabanlı tahmin isteği alındı: {image_id}")
        try:
            # Celery görev varsa async olarak çalıştır
            try:
                from prediction.tasks import process_prediction
                logger.debug(f"Celery görevi başlatılıyor: {image_id}")
                task = process_prediction.delay(image_id, True, str(request.user.id))
                logger.debug(f"Celery görevi başlatıldı: {task.id}")
                return redirect('prediction:results', image_id=image_id)
            except ImportError:
                # Celery yoksa senkron işle
                logger.debug(f"Celery bulunamadı, senkron tahmin yapılıyor: {image_id}")
                
                # Görüntü yolu al
                image_path = image.get('image_path')
                full_path = os.path.join(settings.MEDIA_ROOT, image_path)
                
                if not os.path.exists(full_path):
                    logger.error(f"Görüntü dosyası bulunamadı: {full_path}")
                    return render(request, 'prediction/predict.html', {
                        'image': image,
                        'error': 'Görüntü dosyası bulunamadı'
                    })
                
                # Görüntüyü yükle
                img = cv2.imread(full_path)
                if img is None:
                    logger.error(f"Görüntü yüklenemedi: {full_path}")
                    return render(request, 'prediction/predict.html', {
                        'image': image,
                        'error': 'Görüntü yüklenemedi'
                    })
                
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                
                # Model yükle ve tahmin yap
                from ml.predictor import LungCancerPredictor
                predictor = LungCancerPredictor()
                prediction_result = predictor.predict(img)
                
                # Grad-CAM oluştur
                gradcam_path = None
                try:
                    cam_image = predictor.get_gradcam(img)
                    
                    if cam_image is not None:
                        # Grad-CAM dizinini kontrol et
                        gradcam_dir = os.path.join(settings.MEDIA_ROOT, 'gradcam')
                        if not os.path.exists(gradcam_dir):
                            os.makedirs(gradcam_dir, exist_ok=True)
                            
                        # Dosya adını oluştur
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        gradcam_filename = f"gradcam_{image_id}_{timestamp}.jpg"
                        gradcam_rel_path = f"gradcam/{gradcam_filename}"
                        gradcam_abs_path = os.path.join(settings.MEDIA_ROOT, gradcam_rel_path)
                        
                        # Kaydet
                        cv2.imwrite(gradcam_abs_path, cv2.cvtColor(cam_image, cv2.COLOR_RGB2BGR))
                        
                        # Dosya oluştu mu kontrol et
                        if os.path.exists(gradcam_abs_path):
                            gradcam_path = gradcam_rel_path
                except Exception as grad_error:
                    logger.error(f"Grad-CAM oluşturma hatası: {str(grad_error)}")
                
                # Tahmin sonucunu güncelle
                prediction_result['gradcam_path'] = gradcam_path
                prediction_result['prediction_time'] = datetime.now().strftime('%d.%m.%Y %H:%M')
                
                # MongoDB'ye kaydet
                from prediction.models import ImageSampleRepository
                image_repo = ImageSampleRepository(mongo.db)
                success = image_repo.add_prediction(image_id, prediction_result)
                
                if success:
                    logger.debug(f"Tahmin sonucu başarıyla kaydedildi: {image_id}")
                    return redirect('prediction:results', image_id=image_id)
                else:
                    logger.error(f"Tahmin sonucu kaydedilemedi: {image_id}")
                    return render(request, 'prediction/predict.html', {
                        'image': image,
                        'error': 'Tahmin sonucu kaydedilemedi'
                    })
        except Exception as e:
            # Genel hata durumu
            logger.error(f"Tahmin işlemi başarısız: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return render(request, 'prediction/predict.html', {
                'image': image,
                'error': f"Tahmin işlemi başarısız: {str(e)}"
            })
    
    # GET isteği ise tahmin formunu göster
    logger.debug(f"Tahmin formu görüntüleniyor: {image_id}")
    return render(request, 'prediction/predict.html', {
        'image': image
    })

@login_required
@doctor_or_pathologist_required
def prediction_results(request, image_id):
    """Tahmin sonuçlarını gösterme"""
    mongo = MongoManager()
    
    # Görüntü var mı kontrol et
    try:
        image = mongo.db.image_samples.find_one({'_id': ObjectId(image_id)})
    except:
        return redirect('prediction:case_list')
        
    if not image:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    case_id = image.get('case_id')
    if request.user.user_type not in ['admin'] and case_id:
        try:
            case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
            if case and str(case.get('doctor_id')) != str(request.user.id):
                return redirect('prediction:case_list')
        except:
            pass
    
    # _id'yi id olarak ayarla
    image['id'] = str(image['_id'])
    
    # Tahminleri al
    predictions = image.get('predictions', [])
    prediction = predictions[-1] if predictions else None
    
    if not prediction:
        # Tahmin yoksa, tahmin sayfasına yönlendir
        return redirect('prediction:predict_image', image_id=image_id)
    
    return render(request, 'prediction/results.html', {
        'image': image,
        'prediction': prediction,
        'case_id': case_id,
        'MEDIA_URL': settings.MEDIA_URL,
    })

@login_required
@doctor_or_pathologist_required
def visualize_prediction(request, image_id):
    """Tahmin görselleştirme sayfası"""
    mongo = MongoManager()
    
    # Görüntü var mı kontrol et
    try:
        image = mongo.db.image_samples.find_one({'_id': ObjectId(image_id)})
    except:
        return redirect('prediction:case_list')
        
    if not image:
        return redirect('prediction:case_list')
    
    # Yetki kontrolü
    case_id = image.get('case_id')
    if request.user.user_type not in ['admin'] and case_id:
        try:
            case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
            if case and str(case.get('doctor_id')) != str(request.user.id):
                return redirect('prediction:case_list')
        except:
            pass
    
    # _id'yi id olarak ayarla
    image['id'] = str(image['_id'])
    
    # Tahminleri al
    predictions = image.get('predictions', [])
    prediction = predictions[-1] if predictions else None
    
    if not prediction or not prediction.get('gradcam_path'):
        # Grad-CAM yoksa, tahmin sayfasına yönlendir
        return redirect('prediction:predict_image', image_id=image_id)
    
    return render(request, 'prediction/visualize.html', {
        'image': image,
        'prediction': prediction
    })

@login_required
@doctor_or_pathologist_required
def batch_prediction(request):
    """Toplu tahmin işlemi"""
    # Burada form gösterilecek
    return render(request, 'prediction/batch.html')

@login_required
@doctor_or_pathologist_required
def batch_results(request):
    """Toplu tahmin sonuçları"""
    # Burada sonuçlar listelenecek
    return render(request, 'prediction/batch_results.html')

@login_required
@doctor_or_pathologist_required
def model_info(request):
    """Model bilgileri sayfası"""
    import logging
    logger = logging.getLogger('django')
    
    # Model versiyon, sınıflar, doğruluk oranı gibi bilgiler
    try:
        from ml.predictor import LungCancerPredictor
        predictor = LungCancerPredictor()
        
        model_data = {
            'version': predictor.model_version,
            'name': predictor.model_name,
            'classes': predictor.class_names,
            'cancer_types': predictor.cancer_types,
            'input_shape': predictor.input_shape,
            'description': 'Bu model, histopatolojik görüntülerden akciğer kanseri tiplerini tespit etmek için geliştirilmiş yüksek doğruluklu bir derin öğrenme modelidir.',
            'accuracy': 0.93,  # Örnek değer (gerçek değer modele göre değişebilir)
            'performance': {
                'sensitivity': 0.91,  # Örnek değerler
                'specificity': 0.95,
                'f1_score': 0.92,
                'auc': 0.94
            },
            'last_updated': '2025-05-06'  # Modelin son güncellenme tarihi
        }
        
        # Ekstra model bilgileri (varsa)
        try:
            # TensorFlow/Keras modeli hakkında ek bilgiler
            layers_info = []
            for layer in predictor.model.layers:
                layer_info = {
                    'name': layer.name,
                    'type': layer.__class__.__name__,
                }
                if hasattr(layer, 'output_shape'):
                    # None değerler olmadan output shape'i string'e dönüştür
                    if layer.output_shape:
                        shape_str = str(layer.output_shape)
                        shape_str = shape_str.replace('None', 'Batch')
                        layer_info['output_shape'] = shape_str
                
                layers_info.append(layer_info)
            
            # Tüm katmanları göstermek verimsiz olabilir, son 10 katmanı göster
            model_data['layers'] = layers_info[-10:] if len(layers_info) > 10 else layers_info
            model_data['total_layers'] = len(layers_info)
            
            # Model parametreleri
            trainable_params = sum([tf.keras.backend.count_params(w) for w in predictor.model.trainable_weights])
            non_trainable_params = sum([tf.keras.backend.count_params(w) for w in predictor.model.non_trainable_weights])
            
            model_data['trainable_params'] = trainable_params
            model_data['non_trainable_params'] = non_trainable_params
            model_data['total_params'] = trainable_params + non_trainable_params
            
        except Exception as model_info_error:
            logger.warning(f"Model ek bilgileri alınamadı: {str(model_info_error)}")
        
    except Exception as e:
        logger.error(f"Model bilgileri alınamadı: {str(e)}")
        model_data = {
            'version': 'Bilinmiyor',
            'name': 'EfficientNetV2L_Supreme',
            'classes': ['lung_aca', 'lung_n', 'lung_scc'],
            'cancer_types': {
                'lung_aca': 'Akciğer Adenokarsinomu',
                'lung_scc': 'Akciğer Skuamöz Hücreli Karsinomu',
                'lung_n': 'Normal Akciğer Dokusu'
            },
            'error': str(e)
        }
    
    return render(request, 'prediction/model_info.html', {
        'model': model_data
    })