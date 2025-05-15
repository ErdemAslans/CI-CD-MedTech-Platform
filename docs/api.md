# LungVision AI API Dokümantasyonu

Bu dokümantasyon, LungVision AI platformunun REST API'sini açıklar.

## Temel URL

Tüm API istekleri için temel URL: `https://api.lungvision.ai/api/v1`

## Kimlik Doğrulama

API isteklerinde Token tabanlı kimlik doğrulama kullanılır. Her istek, Authorization header'ında bir token içermelidir:

```http
Authorization: Token your_token_here