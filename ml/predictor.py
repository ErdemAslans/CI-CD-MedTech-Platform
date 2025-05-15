"""
Akciğer kanseri tahmin modülü.

Bu modül, EfficientNetV2L modeli kullanarak akciğer histopatoloji
görüntülerinden kanser tahmini yapar.
"""

import os
import numpy as np
import tensorflow as tf
import cv2
from tensorflow.keras.models import load_model
import logging
from typing import Dict, List, Tuple, Union, Optional, Any

# Log yapılandırması
logger = logging.getLogger('lungvision.predictor')

class LungCancerPredictor:
    """
    Akciğer kanseri tahmini yapan sınıf.
    
    Bu sınıf, eğitilmiş deep learning modelini yükler ve
    görüntü üzerinde tahmin işlemlerini gerçekleştirir.
    """
    
    def __init__(self, model_path: str = None):
        """
        Tahmin ediciyi başlatır ve modeli yükler
        
        Args:
            model_path: Model dosyasının yolu (None ise varsayılan konum kullanılır)
        """
        # Model yolu ayarla
        if model_path is None:
            # Varsayılan model yolu
            # İlk önce Django settings'e bakılır, yoksa sabit konum
            try:
                from django.conf import settings
                if hasattr(settings, 'ML_MODEL_PATH'):
                    model_path = settings.ML_MODEL_PATH
                else:
                    # Proje dizinindeki model
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    model_path = os.path.join(base_dir, 'ml', 'models', 'EfficientNetV2L_supreme.keras')
            except ImportError:
                # Django yüklü değilse veya settings erişilemiyorsa
                # Modül dizinini al
                base_dir = os.path.dirname(os.path.abspath(__file__))
                model_path = os.path.join(base_dir, 'models', 'EfficientNetV2L_supreme.keras')
        
        # Sınıf adları ve kanser türleri
        self.class_names = ['lung_aca', 'lung_n', 'lung_scc']
        self.cancer_types = {
            'lung_aca': 'Akciğer Adenokarsinomu',
            'lung_scc': 'Akciğer Skuamöz Hücreli Karsinomu',
            'lung_n': 'Normal Akciğer Dokusu'
        }
        
        # Model bilgileri
        self.model_version = "1.0.0"
        self.model_name = "EfficientNetV2L_Supreme"
        self.input_shape = (300, 300, 3)
        
        # Modeli yükle
        try:
            logger.info(f"Model yükleniyor: {model_path}")
            self.model = load_model(model_path)
            logger.info("Model başarıyla yüklendi")
            
            # Son konvolüsyon katmanını bul (Grad-CAM için)
            self.last_conv_layer = None
            for layer in reversed(self.model.layers):
                if 'conv' in layer.name and isinstance(layer, tf.keras.layers.Conv2D):
                    self.last_conv_layer = layer.name
                    logger.info(f"Son konvolüsyon katmanı: {self.last_conv_layer}")
                    break
            
            if self.last_conv_layer is None:
                logger.warning("Son konvolüsyon katmanı bulunamadı, Grad-CAM kullanılamayabilir")
            
            # Grad-CAM için model oluştur
            if self.last_conv_layer:
                self.grad_model = tf.keras.models.Model(
                    inputs=[self.model.inputs],
                    outputs=[
                        self.model.get_layer(self.last_conv_layer).output,
                        self.model.output
                    ]
                )
            else:
                self.grad_model = None
            
        except Exception as e:
            logger.error(f"Model yükleme hatası: {str(e)}")
            raise RuntimeError(f"Model yüklenemedi: {str(e)}")
    
    def predict(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Görüntü üzerinde kanser tahmini yapar
        
        Args:
            image: Görüntü verisi (numpy dizisi)
            
        Returns:
            Tahmin sonucu (sınıf, olasılık, vb. içeren sözlük)
        """
        try:
            # Görüntüyü modelimizin beklediği formata dönüştür
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 and image.shape[2] == 3 else image
            
            # Model giriş boyutunu al ve yeniden boyutlandır
            input_shape = self.model.inputs[0].shape
            img_size = (input_shape[2], input_shape[1])  # width, height
            img_resized = cv2.resize(img_rgb, img_size)
            img_normalized = img_resized / 255.0
            
            # Batch formatı için genişlet
            img_batch = np.expand_dims(img_normalized, axis=0)
            
            # Tahmin yap
            predictions = self.model.predict(img_batch, verbose=0)
            
            # En yüksek olasılıklı sınıfı bul
            pred_idx = np.argmax(predictions[0])
            pred_class = self.class_names[pred_idx]
            pred_prob = float(predictions[0][pred_idx])
            
            # Sonuçları yapılandırılmış bir sözlük olarak döndür
            result = {
                'predicted_class': pred_class,
                'predicted_class_display': self.cancer_types.get(pred_class, pred_class),
                'confidence': pred_prob,
                'probabilities': {self.class_names[i]: float(predictions[0][i]) for i in range(len(self.class_names))}
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Tahmin hatası: {str(e)}")
            raise RuntimeError(f"Tahmin işlemi başarısız: {str(e)}")
    
    def get_gradcam(self, image: np.ndarray, pred_index: int = None) -> np.ndarray:
        """
        Görüntü için Grad-CAM ısı haritası oluşturur
        
        Args:
            image: Görüntü verisi (numpy dizisi)
            pred_index: Hedef sınıf indeksi (None ise en yüksek olasılıklı sınıf kullanılır)
            
        Returns:
            Grad-CAM ısı haritası üzerine bindirilmiş görüntü (numpy dizisi)
        """
        if self.grad_model is None:
            logger.warning("Grad-CAM modeli oluşturulmadığı için Grad-CAM ısı haritası oluşturulamıyor")
            return None
        
        try:
            # Görüntüyü modelimizin beklediği formata dönüştür
            img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB) if len(image.shape) == 3 and image.shape[2] == 3 else image
            
            # Model giriş boyutunu al ve yeniden boyutlandır
            input_shape = self.model.inputs[0].shape
            img_size = (input_shape[2], input_shape[1])  # width, height
            img_resized = cv2.resize(img_rgb, img_size)
            img_normalized = img_resized / 255.0
            
            # Batch formatı için genişlet
            img_batch = np.expand_dims(img_normalized, axis=0)
            
            # Eğer pred_index belirtilmemişse, tahmin yap
            if pred_index is None:
                # En yüksek olasılıklı sınıfı bul
                preds = self.model.predict(img_batch, verbose=0)[0]
                pred_index = np.argmax(preds)
            
            # Grad-CAM hesapla
            heatmap = self._make_gradcam_heatmap(img_batch, pred_index)
            
            # Görselleştirme
            cam_image = self._overlay_gradcam(img_normalized, heatmap, alpha=0.6)
            
            return cam_image
            
        except Exception as e:
            logger.error(f"Grad-CAM hatası: {str(e)}")
            return None
    
    def _make_gradcam_heatmap(self, img_array: np.ndarray, pred_index: int = None) -> np.ndarray:
        """
        Grad-CAM ısı haritası oluşturur
        
        Args:
            img_array: Görüntü verisi batch formatında
            pred_index: Hedef sınıf indeksi
            
        Returns:
            Grad-CAM ısı haritası
        """
        if self.grad_model is None:
            logger.warning("Grad model oluşturulmadığı için Grad-CAM hesaplanamıyor.")
            return None

        # Tahmin indeksi kontrolü
        if pred_index is None:
            preds = self.model.predict(img_array, verbose=0)
            pred_index = tf.argmax(preds[0])

        # Gradyan bandı içinde hesaplama yap
        with tf.GradientTape() as tape:
            last_conv_layer_output, preds = self.grad_model(img_array)

            if pred_index is None:
                pred_index = tf.argmax(preds[0])

            class_channel = preds[:, pred_index]

        # Son konv. katmanının sınıf çıktısına göre gradyanı
        grads = tape.gradient(class_channel, last_conv_layer_output)

        # Her kanal için gradyanların ortalaması
        pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))

        # bfloat16 gibi veri tiplerini float32'ye dönüştür
        last_conv_layer_output = tf.cast(last_conv_layer_output, tf.float32)
        pooled_grads = tf.cast(pooled_grads, tf.float32)

        # Son konv. katmanı çıktısını ağırlıklandır ve topla
        last_conv_layer_output = last_conv_layer_output[0]
        heatmap = last_conv_layer_output @ pooled_grads[..., tf.newaxis]
        heatmap = tf.squeeze(heatmap)

        # ReLU ile normalize et
        heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)

        # Numpy array'e dönüştür ve float32'ye çevir
        return heatmap.numpy().astype(np.float32)
    
    def _overlay_gradcam(self, image: np.ndarray, heatmap: np.ndarray, 
                         alpha: float = 0.5, colormap: int = cv2.COLORMAP_JET) -> np.ndarray:
        """
        Isı haritasını görüntü üzerine bindirir
        
        Args:
            image: Görüntü (normalize edilmiş)
            heatmap: Grad-CAM ısı haritası
            alpha: Şeffaflık değeri (0-1 arası)
            colormap: OpenCV renk haritası
            
        Returns:
            Isı haritası üzerine bindirilmiş görüntü
        """
        # Isı haritasını yeniden boyutlandır
        heatmap = cv2.resize(heatmap, (image.shape[1], image.shape[0]))
        heatmap = np.uint8(255 * heatmap)
        
        # Isı haritasına renk uygula
        colored_heatmap = cv2.applyColorMap(heatmap, colormap)
        
        # Görüntüyü BGR'ye dönüştür
        if len(image.shape) == 3 and image.shape[2] == 3:
            img_bgr = image.astype(np.float32)
            
            if np.max(img_bgr) <= 1.0:
                img_bgr = img_bgr * 255
        else:
            raise ValueError("Görüntü 3 kanallı RGB formatında ve orijinal boyutunda olmalı")
        
        # Renkli heatmap ile görüntünün birleştirilmesi
        cam_image = colored_heatmap * alpha + img_bgr * (1 - alpha)
        cam_image = cam_image.astype(np.uint8)
        
        # RGB formatına dönüştür
        cam_image = cv2.cvtColor(cam_image, cv2.COLOR_BGR2RGB)
        
        return cam_image