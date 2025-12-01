import json
import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from .services import dr_service

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])
def home(request):
    """Main application view"""
    if request.method == 'GET':
        return render(request, 'prediction/home.html')
    
    # Handle POST requests (can be used for API endpoints)
    return JsonResponse({'message': 'DR Detection API', 'version': '1.0'})

@csrf_exempt
@require_http_methods(["POST"])
def predict_image(request):
    """Handle image upload and prediction"""
    try:
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'No image file provided'
            }, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        if not image_file.content_type.startswith('image/'):
            return JsonResponse({
                'success': False,
                'error': 'Invalid file type. Please upload an image.'
            }, status=400)
        
        # Validate file size (max 10MB)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'File too large. Maximum size is 10MB.'
            }, status=400)
        
        # Process the image
        result = dr_service.process_image(image_file)
        
        if result.get('success', False):
            # Convert graph path to relative URL if exists
            if result.get('graph_path'):
                graph_filename = result['graph_path'].split('/')[-1]
                result['graph_url'] = f'/media/graphs/{graph_filename}'
                del result['graph_path']
            
            return JsonResponse(result)
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Prediction failed')
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error in predict_image: {e}")
        return JsonResponse({
            'success': False,
            'error': 'An unexpected error occurred during processing.'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'model_loaded': dr_service.model is not None,
        'demo_mode': dr_service.model is None
    })

@csrf_exempt
@require_http_methods(["GET"])
def model_info(request):
    """Get model information"""
    class_info = [
        {'name': label, 'description': get_class_description(label)}
        for label in dr_service.class_labels
    ]
    
    return JsonResponse({
        'model_type': 'Convolutional Neural Network',
        'input_shape': [224, 224, 3],
        'classes': class_info,
        'model_loaded': dr_service.model is not None,
        'demo_mode': dr_service.model is None
    })

def get_class_description(class_name):
    """Get description for each class"""
    descriptions = {
        'No DR': 'No signs of diabetic retinopathy detected',
        'Mild': 'Mild non-proliferative diabetic retinopathy',
        'Moderate': 'Moderate non-proliferative diabetic retinopathy',
        'Severe': 'Severe non-proliferative diabetic retinopathy',
        'Proliferative': 'Proliferative diabetic retinopathy'
    }
    return descriptions.get(class_name, 'Diabetic retinopathy classification')
