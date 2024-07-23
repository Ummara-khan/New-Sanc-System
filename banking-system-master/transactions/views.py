from django.shortcuts import render, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib import messages
from django.http import HttpRequest
from .forms import UploadFileForm
from .models import SanctionRecord, UploadStatistics
from .name_variations import generate_name_variations
from io import TextIOWrapper
from datetime import datetime
import csv
import uuid

from django.utils import timezone
from io import TextIOWrapper
import uuid
import csv
from .models import SanctionRecord, UploadStatistics

from django.utils import timezone
from io import TextIOWrapper
import uuid
import csv
from .models import SanctionRecord, UploadStatistics
from django.contrib import messages

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%B %d, %Y')  # e.g., 'July 19, 2024'
    except ValueError:
        return None

def generate_watch_list_id():
    return SanctionRecord.objects.count() + 1

def process_file(file, list_name, request):
    start_time = timezone.now()
    dataset_id = uuid.uuid4()

    try:
        file_wrapper = TextIOWrapper(file, encoding='utf-8', errors='replace')
    except UnicodeDecodeError as e:
        messages.error(request, f"Error decoding file: {str(e)}")
        return

    reader = csv.DictReader(file_wrapper)
    new_records = 0
    updated_records = 0
    records_to_update = []

    for row in reader:
        record_id = row.get('ID_original')  # Ensure correct field name
        if not record_id:
            continue
        
        created_date = parse_date(row.get('Created Date', ''))
        modified_date = parse_date(row.get('Modified Date', ''))

        if created_date is None:
            created_date = timezone.now()
        
        watch_list_id = row.get('Watchlist ID', generate_watch_list_id())

        # Log the record being processed
        print(f"Processing record ID: {record_id}")

        obj, created = SanctionRecord.objects.update_or_create(
            id=record_id,
            defaults={
                'first_name': row.get('First Name', ''),
                'last_name': row.get('Last Name', ''),
                'list_name': list_name,
                'created_date': created_date,
                'modified_date': modified_date,
                'is_active': row.get('Is_active', 'False') == 'True',
                'id_original': row.get('ID_original', ''),  # Ensure correct field name
                'entity_type': row.get('Entity Type', ''),  # Ensure correct field name
                'identity_numbers': row.get('Identity Number', ''),  # Ensure correct field name
                'identity_types': row.get('Identity Type', ''),  # Ensure correct field name
                'city': row.get('City', ''),
                'country': row.get('Country', ''),
                'watchlist_country': row.get('Watchlist Country', ''),
                'alias': row.get('Alias', ''),
                'alias_type': row.get('Alias Type', ''),
                'watch_list_id': watch_list_id,
                'dataset_id': dataset_id
            }
        )

        if created:
            new_records += 1
        else:
            updated_records += 1

        records_to_update.append(record_id)

    if records_to_update:
        # Ensure records are correctly updated
        SanctionRecord.objects.filter(id__in=records_to_update).update(dataset_id=dataset_id)

    total_records = SanctionRecord.objects.filter(list_name=list_name).count()

    UploadStatistics.objects.update_or_create(
        list_name=list_name,
        defaults={
            'last_import_date': timezone.now().date(),
            'records_added': new_records,
            'records_updated': updated_records,
            'records_deleted': 0,  # You might need to track deletions if applicable
            'total_active_records': total_records,
            'start_time': start_time,
            'end_time': timezone.now(),
        }
    )


def list_management(request: HttpRequest):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            if form.cleaned_data.get('ofac_file'):
                process_file(form.cleaned_data['ofac_file'], 'ofac', request)
            if form.cleaned_data.get('un_file'):
                process_file(form.cleaned_data['un_file'], 'un', request)
            if form.cleaned_data.get('eu_file'):
                process_file(form.cleaned_data['eu_file'], 'eu', request)
                
            statistics = UploadStatistics.objects.all()
            total_added = sum(stat.records_added for stat in statistics)
            total_ofac = next((stat.records_added for stat in statistics if stat.list_name == 'ofac'), 0)
            total_un = next((stat.records_added for stat in statistics if stat.list_name == 'un'), 0)
            total_eu = next((stat.records_added for stat in statistics if stat.list_name == 'eu'), 0)
            
            messages.success(request, f'Total records added: {total_added}. OFAC: {total_ofac}, UN: {total_un}, EU: {total_eu}')
            
            return redirect('transactions:list_management')
    else:
        form = UploadFileForm()

    statistics = UploadStatistics.objects.all()
    context = {
        'form': form,
        'statistics': statistics
    }
    return render(request, 'transactions/list_management.html', context)

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord

from django.core.paginator import Paginator
from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord

from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord

from django.db.models import Count
from django.shortcuts import render
from .models import SanctionRecord

def records_variations(request):
    watch_list_id = request.GET.get('watch_list_id', '')
    id_original = request.GET.get('id_original', '')
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    list_name = request.GET.get('list_name', '')

    sanction_records = SanctionRecord.objects.all()

    if watch_list_id:
        sanction_records = sanction_records.filter(watch_list_id=watch_list_id)
    if id_original:
        sanction_records = sanction_records.filter(id_original=id_original)
    if first_name:
        sanction_records = sanction_records.filter(first_name__icontains=first_name)
    if last_name:
        sanction_records = sanction_records.filter(last_name__icontains=last_name)
    if list_name:
        sanction_records = sanction_records.filter(list_name=list_name)

    # Annotate each record with the count of variations
    sanction_records = sanction_records.annotate(variation_count=Count('namevariation'))

    # Order by id_original in ascending order
    sanction_records = sanction_records.order_by('id_original')

    paginator = Paginator(sanction_records, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Summary of records by list name
    list_summary = SanctionRecord.objects.values('list_name').annotate(total_records=Count('id')).order_by('list_name')

    context = {
        'sanction_records': page_obj.object_list,
        'page_obj': page_obj,
        'watch_list_id': watch_list_id,
        'id_original': id_original,
        'first_name': first_name,
        'last_name': last_name,
        'list_name': list_name,
        'total_records': paginator.count,
        'list_summary': list_summary,
    }
    return render(request, 'transactions/records_variations.html', context)





from django.shortcuts import get_object_or_404, render, redirect
from transactions.models import SanctionRecord, NameVariation

from django.views.decorators.csrf import csrf_exempt



from django.http import JsonResponse

from .forms import NameVariationForm

import logging

logger = logging.getLogger(__name__)

from django.shortcuts import render, get_object_or_404
from .models import SanctionRecord, NameVariation
from .forms import NameVariationForm
import logging

logger = logging.getLogger(__name__)

def view_record(request, record_id, variation_id=None):
    record = get_object_or_404(SanctionRecord, pk=record_id)
    
    aliases = []
    if record.alias and record.alias_type:
        alias_list = record.alias.split('\n')
        alias_type_list = record.alias_type.split('\n')
        aliases = list(zip(alias_list, alias_type_list))
    
    identities = [
        (item.split(':')[0].strip(), item.split(':')[1].strip())
        for item in (record.identity_numbers.split(', ') if record.identity_numbers else [])
        if ':' in item
    ]
    
    variations = NameVariation.objects.filter(sanction_record=record)
    logger.debug(f"Variations: {list(variations.values('variation_id'))}")
    
    specific_variation = None
    if variation_id:
        specific_variation = variations.filter(pk=variation_id).first()
    
    variations_with_status = [
        {
            'variation_id': variation.variation_id,
            'variation': variation.variation,
            'score': variation.score,
            'status': 'Enabled' if variation.is_active else 'Disabled',
            'form': NameVariationForm(instance=variation)  # Form for editing
        }
        for variation in variations
    ]
    
    context = {
        'list_name': record.list_name,
        'record': record,
        'aliases': aliases,
        'identities': identities,
        'variations': variations_with_status,
        'full_name': f"{record.first_name} {record.last_name}",
        'specific_variation': specific_variation
    }
    
    return render(request, 'transactions/view_record.html', context)








from django.shortcuts import render, get_object_or_404, redirect
from .models import NameVariation, SanctionRecord
from .forms import NameVariationForm

def edit_variation(request, variation_id):
    variation = get_object_or_404(NameVariation, id=variation_id)
    record = variation.sanction_record

    if request.method == 'POST':
        form = NameVariationForm(request.POST, instance=variation)
        if form.is_valid():
            form.save()
            return redirect('transactions:view_record', record_id=record.id)
    else:
        form = NameVariationForm(instance=variation)

    context = {
        'variation_id': variation.id,
        'variation': variation,
        'form': form,
        'status': 'Enabled' if variation.is_active else 'Disabled'
    }

    return render(request, 'transactions/edit_variation.html', context)











import uuid
from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import SanctionRecord, NameVariation

import uuid
from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator
from .models import SanctionRecord, NameVariation

def view_variations(request):
    # Initialize variables
    records = SanctionRecord.objects.all()
    data = []

    # Get filtering inputs and selections
    watch_list_id = request.GET.get('watch_list_id', '')
    name_filter = request.GET.get('name', '').strip()
    identity_type_filter = request.GET.get('identity_type', '').strip()
    country_filter = request.GET.get('country', '').strip()

    # Apply filters based on input
    if watch_list_id:
        records = records.filter(watch_list_id=watch_list_id)
    if name_filter:
        records = records.filter(
            Q(first_name__icontains=name_filter) | Q(last_name__icontains=name_filter)
        )
    if identity_type_filter:
        records = records.filter(identity_type__icontains=identity_type_filter)
    if country_filter:
        records = records.filter(country__icontains=country_filter)

    # Generate variations for each record
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        
        # Only generate variations if none exist
        if not existing_variations.exists():
            variations = generate_name_variations(combined_name)
            variations_to_create = [
                NameVariation(
                    sanction_record=record,
                    variation=variation,
                    score=score,
                    test_id=uuid.uuid4()  # Assign unique test_id
                )
                for variation, score in variations.items()
            ]
            NameVariation.objects.bulk_create(variations_to_create)

    # Prepare data for rendering
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        variation_count = NameVariation.objects.filter(sanction_record=record).count()
        
        variations_list = list(NameVariation.objects.filter(sanction_record=record).values('variation_id', 'variation', 'score', 'test_id'))
        data.append({
            'combined_name': combined_name,
            'entity_type': record.entity_type,
            'created_date': record.created_date,
            'variations': variations_list,
            'variation_count': variation_count,  # Corrected count of variations
            'list_name': record.list_name,
            'dataset_id': record.dataset_id,
            'watch_list_id': record.watch_list_id,
        })

    # Paginate data
    paginator = Paginator(data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'transactions/view_variations.html', {
        'page_obj': page_obj,
        'show_data': request.GET.get('generate'),  # Whether to show data based on "Generate" button click
        'watch_list_id': watch_list_id,  # Pass the filter parameter to the template
    })


import csv
from django.http import HttpResponse

def export_variations(request):

    records = SanctionRecord.objects.all()
    data = []

    # Get filtering inputs and selections
    name_filter = request.GET.get('name', '').strip()
    identity_type_filter = request.GET.get('identity_type', '').strip()
    country_filter = request.GET.get('country', '').strip()

    # Initialize the HTTP response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="variations_export.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'Name', 'Test ID', 'Dataset ID', 'Entity Type', 'List Name', 
        'Variation ID', 'Variation', 'Score', 'Number of Entries', 
        'Filter Option', 'System Option', 'Test Option', 'Complexity Level'
    ])
    
    # Get filter values
    num_entries = request.GET.get('num_entries', '')
    filter_option = request.GET.get('filter_option', '')
    system_option = request.GET.get('system_option', '')
    test_option = request.GET.get('test_option', '')
    complexity_level = request.GET.get('complexity_level', '')

    # Query records based on filters
    records = SanctionRecord.objects.all()
    if filter_option:
        if filter_option == 'name':
            records = records.filter(first_name__icontains=name_filter) | records.filter(last_name__icontains=name_filter)
        elif filter_option == 'identity_type':
            records = records.filter(identity_type__icontains=identity_type_filter)
        elif filter_option == 'country':
            records = records.filter(country__icontains=country_filter)
    
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        for variation in existing_variations:
            writer.writerow([
                combined_name,
                variation.test_id,
                record.dataset_id,
                record.entity_type,
                record.list_name,
                variation.variation_id,
                variation.variation,
                variation.score,
                num_entries,
                filter_option,
                system_option,
                test_option,
                complexity_level
            ])
    
    return response





# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import SanctionRecordDetail
import random

def generate_test_data(request):
    if request.method == 'POST':
        num_entries = int(request.POST.get('num_entries', 0))
        selected_fields = request.POST.getlist('fields')  # e.g., ['name', 'country', 'identity']
        
        if num_entries > 0:
            # Fetch random records
            all_records = list(SanctionRecordDetail.objects.all())
            random_records = random.sample(all_records, min(num_entries, len(all_records)))
            
            # Prepare the response data
            data = []
            for record in random_records:
                record_data = {
                    'name': record.name if 'name' in selected_fields else '',
                    'entity_type': record.entity_type if 'entity' in selected_fields else '',
                    'list_name': record.list_name if 'list_name' in selected_fields else '',
                    'score': record.score if 'score' in selected_fields else '',
                    'identity_type': record.sanction_record.identity_type if 'identity' in selected_fields else '',
                    'id': record.sanction_record.id_original if 'identity' in selected_fields else '',
                    'country': record.sanction_record.country if 'country' in selected_fields else ''
                }
                data.append(record_data)
            
            return JsonResponse({'data': data})
    
    return render(request, 'transactions/generate_test_data.html')



import csv
from django.http import HttpResponse
from .models import NameVariation  # Update with your actual model

def export_variations_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="variations.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Identity Type', 'Country'])  # Update with your actual column names

    variations = NameVariation.objects.all()  # Add filtering logic if needed
    for variation in variations:
        writer.writerow([variation.name, variation.identity_type, variation.country])  # Update with your actual fields

    return response




from django.core.paginator import Paginator
from django.shortcuts import render
from .models import SanctionRecord, NameVariation
from django.core.paginator import Paginator
from django.shortcuts import render
from .models import SanctionRecord, NameVariation


def all_variations(request):
    records = SanctionRecord.objects.all()
    data = []
    
    for record in records:
        combined_name = f"{record.first_name} {record.last_name}"
        
        # Check if variations exist for this record
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        if not existing_variations.exists():
            # Generate variations if none exist
            variations = generate_name_variations(combined_name)
            
            variations_to_create = [
                NameVariation(
                    sanction_record=record,
                    variation=variation,
                    score=score
                )
                for variation, score in variations.items()
            ]
            
            # Bulk create new variations
            NameVariation.objects.bulk_create(variations_to_create)
        
        # Re-fetch variations for the view
        existing_variations = NameVariation.objects.filter(sanction_record=record)
        variations_list = list(existing_variations.values('variation', 'score'))
        
        data.append({
            'combined_name': combined_name,
            'entity_type': record.entity_type,
            'created_date': record.created_date,
            'variations': variations_list
        })

    paginator = Paginator(data, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'transactions/all_variations.html', {'page_obj': page_obj})



















from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import NameVariation

@csrf_exempt
def handle_ajax_request(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        variation_id = request.POST.get('id')
        
        try:
            variation = NameVariation.objects.get(id=variation_id)
            
            if action == 'delete':
                variation.delete()
                return JsonResponse({'success': True})

            elif action == 'disable':
                variation.status = request.POST.get('status')
                variation.save()
                return JsonResponse({'success': True})

        except NameVariation.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Variation not found'})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})













