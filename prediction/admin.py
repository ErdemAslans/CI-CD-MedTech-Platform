from django.contrib import admin
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import path
from django.utils.html import format_html
import json
from bson import json_util
from core.db import MongoManager

class MongoDBModelAdmin:
    """MongoDB koleksiyonları için özel admin sınıfı"""
    
    list_display = []
    search_fields = []
    list_filter = []
    
    # MongoDB bağlantısı
    mongo = MongoManager()
    
    def get_collection(self):
        """MongoDB koleksiyonunu döndürür"""
        return self.mongo.db[self.collection_name]

class PatientCaseAdmin(admin.ModelAdmin):
    """Patient Case Admin - MongoDB view"""
    
    change_list_template = 'admin/prediction/patientcase/change_list.html'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('', self.admin_site.admin_view(self.changelist_view), name='prediction_patientcase_changelist'),
            path('<str:case_id>/', self.admin_site.admin_view(self.detail_view), name='prediction_patientcase_detail'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request):
        """Vaka listesi görünümü"""
        mongo = MongoManager()
        
        # Tüm vakaları al
        cases = list(mongo.db.patient_cases.find().sort('created_at', -1))
        
        # ObjectId'leri string'e dönüştür
        for case in cases:
            case['_id'] = str(case['_id'])
        
        context = {
            'title': 'Patient Cases',
            'cases': cases,
            'cl': {
                'opts': {
                    'app_label': 'prediction',
                    'model_name': 'patientcase',
                }
            }
        }
        
        return render(request, self.change_list_template, context)
    
    def detail_view(self, request, case_id):
        """Vaka detay görünümü"""
        mongo = MongoManager()
        
        # Vakayı al
        from bson import ObjectId
        case = mongo.db.patient_cases.find_one({'_id': ObjectId(case_id)})
        
        if not case:
            return HttpResponse("Case not found", status=404)
        
        # ObjectId'yi string'e dönüştür
        case['_id'] = str(case['_id'])
        
        # Vakaya ait görüntüleri al
        images = list(mongo.db.image_samples.find({'case_id': case_id}))
        
        for image in images:
            image['_id'] = str(image['_id'])
        
        context = {
            'title': f"Case Detail: {case.get('patient_id', '')}",
            'case': case,
            'images': images,
            'case_json': json.dumps(case, default=json_util.default, indent=2),
            'cl': {
                'opts': {
                    'app_label': 'prediction',
                    'model_name': 'patientcase',
                }
            }
        }
        
        return render(request, 'admin/prediction/patientcase/detail.html', context)