"""OVC Care views."""
from django.shortcuts import render
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from datetime import (date, datetime)
from .forms import OVCSearchForm, OVCRegistrationForm, OVCExtraInfoForm
from cpovc_registry.models import (
    RegPerson, RegPersonsGuardians, RegPersonsSiblings, RegPersonsExternalIds,
    RegPersonsAuditTrail)
from cpovc_main.functions import (get_dict, get_days_difference)
from .models import (
    OVCRegistration, OVCHHMembers, OVCEligibility, OVCViralload, OVCVLTracker)
from .functions import (
    ovc_registration, get_hh_members, get_ovcdetails, gen_cbo_id, search_ovc,
    search_master, get_school, get_health, manage_checkins, ovc_management,
    get_exit_org, save_health, save_hh_info, get_extra_info)
from cpovc_auth.decorators import is_allowed_ous

from cpovc_forms.models import (
    OVCCareEvents, OVCHivStatus, OVCCareBenchmarkScore, OVCBenchmarkMonitoring)

from .functions import PersonObj, perform_exit, dates_difference
from cpovc_auth.decorators import validate_ovc
from cpovc_auth.models import AppUser

from cpovc_api.models import MetadataManagement

from .params import fms


@login_required(login_url='/')
def ovc_home(request):
    """Some default page for Server Errors."""
    try:
        rid = 0
        pe = request.GET.get('P', '')
        # person_id = request.GET.get('person_id', '')
        reqid = request.GET.get('id', '')
        offset = request.GET.get('offset', '')
        limit = request.GET.get('limit', '')
        if reqid and offset and limit:
            rid = 2
        if request.method == 'POST' or rid:
            aid = request.POST.get('id')
            act_id = int(aid) if aid else 0
            action_id = rid if rid else act_id
            if action_id in [1, 2, 3]:
                msg, chs = manage_checkins(request, rid)
                results = {'status': 0, 'message': msg, 'checkins': chs}
                if rid == 2:
                    results = chs
                return JsonResponse(results, content_type='application/json',
                                    safe=False)
            elif action_id in [4]:
                msg = 'Record deleted successfully.'
                cid = request.POST.get('cid')
                OVCRegistration.objects.filter(id=cid).delete()
                results = {'status': 0,
                           'message': 'Record deleted successfully.'}
                return JsonResponse(results, content_type='application/json',
                                    safe=False)
            form = OVCSearchForm(data=request.POST)
            ovcs = search_ovc(request)

            check_fields = ['sex_id']
            vals = get_dict(field_name=check_fields)

            return render(request, 'ovc/home.html',
                          {'form': form, 'ovcs': ovcs,
                           'vals': vals})
        form = OVCSearchForm()
        return render(
            request, 'ovc/home.html',
            {'form': form, 'status': 200, 'pe': pe})
    except Exception as e:
        raise e


def ovc_search(request):
    """Method to do ovc search."""
    try:
        results = search_master(request)
    except Exception as e:
        print('error with search - %s' % (str(e)))
        return JsonResponse(results, content_type='application/json',
                            safe=False)
    else:
        return JsonResponse(results, content_type='application/json',
                            safe=False)


@login_required(login_url='/')
@is_allowed_ous(['RGM', 'RGU', 'DSU', 'STD'])
def ovc_register(request, id):
    """Some default page for Server Errors."""
    try:
        ovc_id = int(id)
        ovc = get_ovcdetails(ovc_id)
        params, gparams = {}, {}
        initial = {}
        # Details
        child = RegPerson.objects.get(is_void=False, id=id)
        # Get guardians
        # Get guardians - Not working
        '''
        guardians = RegPersonsGuardians.objects.filter(
            is_void=False, child_person_id=child.id)
        print('Guardians', guardians)
        '''
        # Reverse relationship
        osiblings = RegPersonsSiblings.objects.select_related().filter(
            sibling_person_id=ovc_id, is_void=False,
            date_delinked=None)
        # .exclude(sibling_person_id=id)
        child_ids = [gd.child_person_id for gd in osiblings]
        child_ids.append(ovc_id)
        guardians = RegPersonsGuardians.objects.select_related().filter(
            child_person_id__in=child_ids, is_void=False, date_delinked=None)
        # Get siblings
        siblings = RegPersonsSiblings.objects.filter(
            is_void=False, child_person_id=child.id)
        print('p', params, 'gp', gparams)
        guids, chids = [], []
        for guardian in guardians:
            guids.append(guardian.guardian_person_id)
        guids.append(child.id)
        for sibling in siblings:
            chids.append(sibling.sibling_person_id)
        pids = {'guids': guids, 'chids': chids}
        print(pids)
        # Existing
        extids = RegPersonsExternalIds.objects.filter(
            person_id__in=guids)
        for extid in extids:
            if extid.person_id == child.id:
                params[extid.identifier_type_id] = extid.identifier
            else:
                gkey = '%s_%s' % (extid.person_id, extid.identifier_type_id)
                gparams[gkey] = extid.identifier
        if request.method == 'POST':
            form = OVCRegistrationForm(guids=pids, data=request.POST)
            status = ovc_registration(request, ovc_id)
            msg = status['status_msg']
            msg_id = status['status_id']
            # msg = "OVC Registration completed successfully"
            if msg_id:
                messages.error(request, msg)
            else:
                messages.info(request, msg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        else:
            cbo_id = ovc.child_cbo_id
            cbo_uid = gen_cbo_id(cbo_id, ovc_id)
            initial['cbo_uid'] = cbo_uid
            initial['cbo_id'] = cbo_id
            initial['cbo_uid_check'] = cbo_uid
            if 'ISOV' in params:
                initial['bcert_no'] = params['ISOV']
                initial['has_bcert'] = 'on'
            form = OVCRegistrationForm(
                guids=pids, initial=initial)
        # Check users changing ids in urls
        ovc_detail = get_hh_members(ovc_id)
        if ovc_detail:
            msg = "OVC already registered. Visit edit page."
            messages.error(request, msg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        # Class levels
        levels = {}
        levels["SLNS"] = []
        levels["SLEC"] = ["BABY,Baby Class", "MIDC,Middle Class",
                          "PREU,Pre-Unit"]
        levels["SLPR"] = ["CLS1,Class 1", "CLS2,Class 2", "CLS3,Class 3",
                          "CLS4,Class 4", "CLS5,Class 5", "CLS6,Class 6",
                          "CLS7,Class 7", "CLS8,Class 8"]
        levels["SLSE"] = ["FOM1,Form 1", "FOM2,Form 2", "FOM3,Form 3",
                          "FOM4,Form 4", "FOM5,Form 5", "FOM6,Form 6"]
        levels["SLUN"] = ["YER1,Year 1", "YER2,Year 2", "YER3,Year 3",
                          "YER4,Year 4", "YER5,Year 5", "YER6,Year 6"]
        levels["SLTV"] = ["TVC1,Year 1", "TVC2,Year 2", "TVC3,Year 3",
                          "TVC4,Year 4", "TVC5,Year 5"]
        # Re-usable values
        check_fields = ['relationship_type_id']
        vals = get_dict(field_name=check_fields)
        return render(request, 'ovc/register_child.html',
                      {'form': form, 'status': 200, 'child': child,
                       'guardians': guardians, 'siblings': siblings,
                       'vals': vals, 'extids': gparams, 'ovc': ovc,
                       'levels': levels})
    except Exception as e:
        print("error with OVC registration - %s" % (str(e)))
        raise e


@login_required(login_url='/')
@validate_ovc([])
# @is_allowed_ous(['RGM', 'RGU', 'DSU', 'STD'])
def ovc_edit(request, id):
    """Some default page for Server Errors."""
    try:
        ovc_id = int(id)
        date_reg = None
        if request.method == 'POST':
            status = ovc_registration(request, ovc_id, 1)
            msg = status['status_msg']
            msg_id = status['status_id']
            # Save external ids from here
            if msg_id:
                imsg = "Other OVC Registration details edited successfully"
                messages.error(request, msg)
            else:
                imsg = "OVC Registration details edited successfully"
            messages.info(request, imsg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        exit_org_name = get_exit_org(ovc_id)
        bcert = 'on' if creg.has_bcert else ''
        disb = 'on' if creg.is_disabled else ''
        exited = '' if creg.is_active else 'on'
        reg_date = creg.registration_date
        child.caretaker = creg.caretaker_id
        child.cbo = creg.child_cbo.org_unit_name
        child.chv_name = creg.child_chv.full_name
        params = {}
        gparams = {}
        siblings = 0
        # Get house hold
        hhold = OVCHHMembers.objects.filter(
            is_void=False, person_id=child.id).order_by('-date_linked').first()
        hhid = hhold.house_hold_id
        head_id = hhold.house_hold.head_person_id
        cgs = RegPerson.objects.filter(id=head_id)
        hhmqs = OVCHHMembers.objects.filter(
            is_void=False, house_hold_id=hhid).order_by("-hh_head")
        # Viral Load

        vloads = OVCViralload.objects.filter(
            is_void=False, person_id=ovc_id).order_by("-viral_date")
        vlist = []
        for vl in vloads:
            obj = {}
            obj['viral_date'] = vl.viral_date
            obj['viral_load'] = vl.viral_load
            if vl.viral_date:
                delta = get_days_difference(vl.viral_date)
                if (delta) < 183:
                    obj['status'] = 0
                else:
                    obj['status'] = 1
            else:
                obj['status'] = 1

            vlist.append(obj)
        # add caregivers hiv status
        hhmembers, hhm_ids = [], []
        hhms = hhmqs.exclude(person_id=child.id)
        for hhm in hhms:
            hhm_ids.append(hhm.person_id)
            hhmembers.append(hhm)
        # After upgrade CG is missing on Members table - hacking this
        m_type = 'CCGV'
        gtypes = RegPersonsGuardians.objects.filter(
            child_person_id=child.id, guardian_person_id=head_id,
            is_void=False)
        for gtype in gtypes:
            m_type = gtype.relationship
        pobj = PersonObj()
        pobj.member_type = m_type
        pobj.member_alive = 'AYES'
        for cg in cgs:
            if cg.id not in hhm_ids:
                pobj.person = cg
                pobj.person_id = cg.id
                hhmembers.append(pobj)
        # Get guardians and siblings ids
        guids, chids = [], []
        ctaker = 0
        for hh_member in hhms:
            member_type = hh_member.member_type
            member_head = hh_member.hh_head
            if member_head:
                ctaker = hh_member.person_id
            if member_type == 'TBVC' or member_type == 'TOVC':
                chids.append(hh_member.person_id)
                siblings += 1
            else:
                guids.append(hh_member.person_id)
        guids.append(child.id)
        pids = {'guids': guids, 'chids': chids}
        extids = RegPersonsExternalIds.objects.filter(
            person_id__in=guids, is_void=False)
        for extid in extids:
            if extid.person_id == child.id:
                params[extid.identifier_type_id] = extid.identifier
            else:
                gkey = '%s_%s' % (extid.person_id, extid.identifier_type_id)
                gparams[gkey] = extid.identifier
        # Get health information
        ccc_no, date_linked, art_status = '', '', ''
        facility_id, facility = '', ''
        if creg.hiv_status in ['HSTP', 'HHEI']:
            health = get_health(ovc_id)
            if health:
                ccc_no = health.ccc_number
                date_linked = health.date_linked.strftime('%d-%b-%Y')
                art_status = health.art_status
                facility_id = health.facility_id
                facility = "%s - %s" % (
                    health.facility.facility_code, health.facility.facility_name)
        # Get School information
        sch_class, sch_adm_type = '', ''
        school_id, school = '', ''
        if creg.school_level != 'SLNS':
            school = get_school(ovc_id)
            if school:
                sch_class = school.school_class
                sch_adm_type = school.admission_type
                school_id = school.school_id
                school = school.school.school_name
        bcert_no = params['ISOV'] if 'ISOV' in params else ''
        ncpwd_no = params['IPWD'] if 'IPWD' in params else ''
        # Additional Identifiers
        nemis_id = params['INEM'] if 'INEM' in params else ''
        nupi_id = params['IUPI'] if 'IUPI' in params else ''
        dreams_id = params['IDRM'] if 'IDRM' in params else ''
        drms = 'on' if dreams_id else ''
        # Eligibility
        criterias = OVCEligibility.objects.filter(
            is_void=False, person_id=child.id).values_list(
            'criteria', flat=True)
        if reg_date:
            date_reg = reg_date.strftime('%d-%b-%Y')
        exit_date = None
        if creg.exit_date:
            exit_date = creg.exit_date.strftime('%d-%b-%Y')

        all_values = {'reg_date': date_reg, 'cbo_uid': creg.org_unique_id,
                      'cbo_uid_check': creg.org_unique_id,
                      'has_bcert': bcert, 'disb': disb,
                      'bcert_no': bcert_no, 'ncpwd_no': ncpwd_no,
                      'immunization': creg.immunization_status,
                      'school_level': creg.school_level, 'facility': facility,
                      'facility_id': facility_id, 'school_class': sch_class,
                      'school_name': school, 'school_id': school_id,
                      'admission_type': sch_adm_type,
                      'hiv_status': creg.hiv_status, 'link_date': date_linked,
                      'ccc_number': ccc_no, 'art_status': art_status,
                      'eligibility': list(criterias), 'is_exited': exited,
                      'exit_reason': creg.exit_reason,
                      'ovc_exit_reason': creg.exit_reason,
                      'exit_date': exit_date, 'dreams_id': dreams_id,
                      'exit_org_name': exit_org_name,
                      'is_dreams_enrolled': drms, 'nupi_id': nupi_id,
                      'nemis_id': nemis_id}
        form = OVCRegistrationForm(guids=pids, data=all_values)
        for hhm in hhms:
            status_id = 'status_%s' % (hhm.person_id)
            all_values['a%s' % (status_id)] = hhm.member_alive
            all_values['g%s' % (status_id)] = hhm.hiv_status
            all_values['sg%s' % (status_id)] = hhm.hiv_status
        # Class levels
        levels = {}
        levels["SLNS"] = []
        levels["SLEC"] = ["BABY,Baby Class", "MIDC,Middle Class",
                          "PREU,Pre-Unit"]
        levels["SLPR"] = ["CLS1,Class 1", "CLS2,Class 2", "CLS3,Class 3",
                          "CLS4,Class 4", "CLS5,Class 5", "CLS6,Class 6",
                          "CLS7,Class 7", "CLS8,Class 8"]
        levels["SLSE"] = ["FOM1,Form 1", "FOM2,Form 2", "FOM3,Form 3",
                          "FOM4,Form 4", "FOM5,Form 5", "FOM6,Form 6"]
        levels["SLUN"] = ["YER1,Year 1", "YER2,Year 2", "YER3,Year 3",
                          "YER4,Year 4", "YER5,Year 5", "YER6,Year 6"]
        levels["SLTV"] = ["TVC1,Year 1", "TVC2,Year 2", "TVC3,Year 3",
                          "TVC4,Year 4", "TVC5,Year 5"]
        # Re-usable values

        check_fields = ['relationship_type_id', 'exit_reason_id']
        vals = get_dict(field_name=check_fields)
        hiv_data = OVCHivStatus.objects.filter(
            person_id=ovc_id).order_by('date_of_event')

        # date manenos
        date_langu = datetime.now().month

        return render(request, 'ovc/edit_child.html',
                      {'form': form, 'status': 200, 'child': child,
                       'vals': vals, 'hhold': hhold, 'extids': gparams,
                       'hhmembers': hhmembers, 'levels': levels,
                       'sch_class': sch_class, 'siblings': siblings,
                       'ctaker': ctaker, 'vloads': vlist, 'mydate': date_langu,
                       'hiv_data': hiv_data, 'creg': creg})
    except Exception as e:
        print("error with OVC viewing - %s" % (str(e)))
        # raise e
        msg = "Error occured during ovc edit"
        messages.error(request, msg)
        form = OVCSearchForm()
        return render(request, 'ovc/home.html', {'form': form, 'status': 200})


@login_required(login_url='/')
@is_allowed_ous(['RGM', 'RGU', 'DSU', 'STD'])
def ovc_edit_old(request, id):
    """Some default page for Server Errors."""
    try:
        ovc_id = int(id)
        date_reg = None
        if request.method == 'POST':
            ovc_registration(request, ovc_id, 1)
            # Save external ids from here
            msg = "OVC Registration details edited successfully"
            messages.info(request, msg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        exit_org_name = get_exit_org(ovc_id)
        bcert = 'on' if creg.has_bcert else ''
        disb = 'on' if creg.is_disabled else ''
        exited = '' if creg.is_active else 'on'
        reg_date = creg.registration_date
        child.caretaker = creg.caretaker_id
        child.cbo = creg.child_cbo.org_unit_name
        child.chv_name = creg.child_chv.full_name
        params = {}
        gparams = {}
        siblings = 0
        # Get house hold
        hhold = OVCHHMembers.objects.get(
            is_void=False, person_id=child.id)
        hhid = hhold.house_hold_id
        hhmqs = OVCHHMembers.objects.filter(
            is_void=False, house_hold_id=hhid).order_by("-hh_head")
        # Viral Load

        vloads = OVCViralload.objects.filter(
            is_void=False, person_id=ovc_id).order_by("-viral_date")
        vlist = []
        for vl in vloads:
            obj = {}
            obj['viral_date'] = vl.viral_date
            obj['viral_load'] = vl.viral_load

            delta = get_days_difference(vl.viral_date)
            print(delta)

            if (delta) < 183:
                obj['status'] = 0
            else:
                obj['status'] = 1

            vlist.append(obj)
        # add caregivers hiv status
        hhmembers = hhmqs.exclude(person_id=child.id)
        # Get guardians and siblings ids
        guids, chids = [], []
        ctaker = 0
        for hh_member in hhmembers:
            member_type = hh_member.member_type
            member_head = hh_member.hh_head
            if member_head:
                ctaker = hh_member.person_id
            if member_type == 'TBVC' or member_type == 'TOVC':
                chids.append(hh_member.person_id)
                siblings += 1
            else:
                guids.append(hh_member.person_id)
        guids.append(child.id)
        pids = {'guids': guids, 'chids': chids}
        extids = RegPersonsExternalIds.objects.filter(
            person_id__in=guids)
        for extid in extids:
            if extid.person_id == child.id:
                params[extid.identifier_type_id] = extid.identifier
            else:
                gkey = '%s_%s' % (extid.person_id, extid.identifier_type_id)
                gparams[gkey] = extid.identifier
        # Get health information
        ccc_no, date_linked, art_status = '', '', ''
        facility_id, facility = '', ''
        if creg.hiv_status in ['HSTP', 'HHEI']:
            health = get_health(ovc_id)
            if health:
                ccc_no = health.ccc_number
                date_linked = health.date_linked.strftime('%d-%b-%Y')
                art_status = health.art_status
                facility_id = health.facility_id
                facility = health.facility.facility_name
        # Get School information
        sch_class, sch_adm_type = '', ''
        school_id, school = '', ''
        if creg.school_level != 'SLNS':
            school = get_school(ovc_id)
            if school:
                sch_class = school.school_class
                sch_adm_type = school.admission_type
                school_id = school.school_id
                school = school.school.school_name
        bcert_no = params['ISOV'] if 'ISOV' in params else ''
        ncpwd_no = params['IPWD'] if 'IPWD' in params else ''
        # Eligibility
        criterias = OVCEligibility.objects.filter(
            is_void=False, person_id=child.id).values_list(
            'criteria', flat=True)
        if reg_date:
            date_reg = reg_date.strftime('%d-%b-%Y')
        exit_date = None
        if creg.exit_date:
            exit_date = creg.exit_date.strftime('%d-%b-%Y')

        all_values = {'reg_date': date_reg, 'cbo_uid': creg.org_unique_id,
                      'cbo_uid_check': creg.org_unique_id,
                      'has_bcert': bcert, 'disb': disb,
                      'bcert_no': bcert_no, 'ncpwd_no': ncpwd_no,
                      'immunization': creg.immunization_status,
                      'school_level': creg.school_level, 'facility': facility,
                      'facility_id': facility_id, 'school_class': sch_class,
                      'school_name': school, 'school_id': school_id,
                      'admission_type': sch_adm_type,
                      'hiv_status': creg.hiv_status, 'link_date': date_linked,
                      'ccc_number': ccc_no, 'art_status': art_status,
                      'eligibility': list(criterias), 'is_exited': exited,
                      'exit_reason': creg.exit_reason,
                      'ovc_exit_reason': creg.exit_reason,
                      'exit_date': exit_date,
                      'exit_org_name': exit_org_name}
        form = OVCRegistrationForm(guids=pids, data=all_values)
        for hhm in hhmembers:
            status_id = 'status_%s' % (hhm.person_id)
            all_values['a%s' % (status_id)] = hhm.member_alive
            all_values['g%s' % (status_id)] = hhm.hiv_status
            all_values['sg%s' % (status_id)] = hhm.hiv_status
        # Class levels
        levels = {}
        levels["SLNS"] = []
        levels["SLEC"] = ["BABY,Baby Class", "MIDC,Middle Class",
                          "PREU,Pre-Unit"]
        levels["SLPR"] = ["CLS1,Class 1", "CLS2,Class 2", "CLS3,Class 3",
                          "CLS4,Class 4", "CLS5,Class 5", "CLS6,Class 6",
                          "CLS7,Class 7", "CLS8,Class 8"]
        levels["SLSE"] = ["FOM1,Form 1", "FOM2,Form 2", "FOM3,Form 3",
                          "FOM4,Form 4", "FOM5,Form 5", "FOM6,Form 6"]
        levels["SLUN"] = ["YER1,Year 1", "YER2,Year 2", "YER3,Year 3",
                          "YER4,Year 4", "YER5,Year 5", "YER6,Year 6"]
        levels["SLTV"] = ["TVC1,Year 1", "TVC2,Year 2", "TVC3,Year 3",
                          "TVC4,Year 4", "TVC5,Year 5"]
        # Re-usable values

        check_fields = ['relationship_type_id']
        vals = get_dict(field_name=check_fields)
        hiv_data = OVCHivStatus.objects.filter(
            person_id=ovc_id).order_by('date_of_event')

        # date manenos
        date_langu = datetime.now().month

        return render(request, 'ovc/edit_child.html',
                      {'form': form, 'status': 200, 'child': child,
                       'vals': vals, 'hhold': hhold, 'extids': gparams,
                       'hhmembers': hhmembers, 'levels': levels,
                       'sch_class': sch_class, 'siblings': siblings,
                       'ctaker': ctaker, 'vloads': vlist, 'mydate': date_langu,
                       'hiv_data': hiv_data})
    except Exception as e:
        print("error with OVC viewing - %s" % (str(e)))
        # raise e
        msg = "Error occured during ovc edit"
        messages.error(request, msg)
        form = OVCSearchForm()
        return render(request, 'ovc/home.html', {'form': form, 'status': 200})


@login_required(login_url='/')
@validate_ovc([])
# @is_allowed_ous(['RGM', 'RGU', 'DSU', 'STD'])
def ovc_view(request, id):
    """Some default page for Server Errors."""
    try:
        aid = 0
        reqid = request.GET.get('id', '')
        offset = request.GET.get('offset', '')
        limit = request.GET.get('limit', '')
        if reqid and offset and limit:
            aid = 2
        if request.method == 'POST' or aid:
            msg, chs = manage_checkins(request, aid)
            results = {'status': 0, 'message': msg, 'checkins': chs}
            if aid == 2:
                results = chs
            return JsonResponse(results, content_type='application/json',
                                safe=False)
        ovc_id = int(id)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        caregiver_id = creg.caretaker_id
        days = 0
        if not creg.is_active and creg.exit_date:
            edate = creg.exit_date
            tdate = date.today()
            days = (tdate - edate).days
        print('exit days', days)
        allow_edit = False if days > 90 else True
        params = {}
        gparams = {}
        # Get guardians
        guardians = RegPersonsGuardians.objects.filter(
            is_void=False, child_person_id=child.id)
        guids = []
        for guardian in guardians:
            guids.append(guardian.guardian_person_id)
        guids.append(child.id)
        extids = RegPersonsExternalIds.objects.filter(
            person_id__in=guids, is_void=False)
        for extid in extids:
            if extid.person_id == child.id:
                params[extid.identifier_type_id] = extid.identifier
            else:
                gkey = '%s_%s' % (extid.person_id, extid.identifier_type_id)
                gparams[gkey] = extid.identifier
        # Health details
        health = {}
        if creg.hiv_status in ['HSTP', 'HHEI']:
            health = get_health(ovc_id)
        # School details
        school = {}
        if creg.school_level != 'SLNS':
            school = get_school(ovc_id)
        # Get house hold
        hhold = OVCHHMembers.objects.filter(
            is_void=False, person_id=child.id).order_by('-date_linked').first()
        # Get HH members
        hhid = hhold.house_hold_id
        hhmqs = OVCHHMembers.objects.filter(
            is_void=False, house_hold_id=hhid).order_by("-person_id")
        hhmembers = hhmqs.exclude(person_id=child.id).distinct("person_id")
        # Viral load
        vload = OVCViralload.objects.filter(
            is_void=False, person_id=ovc_id).order_by("-viral_date")[:1]
        vl_sup, v_val, v_dt = 'Missing', None, None
        if vload:
            for vl in vload:
                v_val = vl.viral_load
                v_dt = vl.viral_date
            vl_sup = 'YES' if not v_val or v_val < 1000 else 'NO'
        print(v_dt)
        # Get siblings
        siblings = RegPersonsSiblings.objects.filter(
            is_void=False, child_person_id=child.id)
        # Get services
        servs = {'FSAM': 'f1a', 'FCSI': 'fcsi', 'FHSA': 'fhva',
                 'cpr': 'cpr', 'wba': 'wba', 'CPAR': 'CPAR', 'WBG': 'WBG',
                 'FM1B': 'f1b'}
        services = {'f1a': 0, 'fcsi': 0, 'fhva': 0, 'cpr': 0,
                    'wba': 0, 'CPAR': 0, 'WBG': 0, 'f1b': 0}
        sqs = OVCCareEvents.objects.filter(
            Q(person_id=child.id) | Q(house_hold_id=hhid))
        sqs = sqs.filter(is_void=False).values(
            'event_type_id').annotate(
                total=Count('event_type_id')).order_by('total')
        for serv in sqs:
            item = serv['event_type_id']
            item_count = serv['total']
            if item in servs:
                item_key = servs[item]
                services[item_key] = item_count
        # Re-usable values
        check_fields = ['relationship_type_id', 'school_level_id',
                        'hiv_status_id', 'immunization_status_id',
                        'art_status_id', 'school_type_id',
                        'class_level_id', 'eligibility_criteria_id']
        vals = get_dict(field_name=check_fields)
        wellbeing_services = {}
        wellbeing_services['wba'] = services['wba']
        wellbeing_services['WBG'] = services['WBG']
        child_hiv_status = creg.hiv_status
        criterias = OVCEligibility.objects.filter(
            is_void=False, person_id=child.id)
        try:
            care_giver = RegPerson.objects.get(id=caregiver_id)
        except RegPerson.DoesNotExist:
            care_giver = None
            print('Caregiver does not exist for child: %s' % child.id)
        return render(request, 'ovc/view_child.html',
                      {'status': 200, 'child': child, 'params': params,
                       'child_hiv_status': child_hiv_status,
                       'guardians': guardians, 'siblings': siblings,
                       'vals': vals, 'hhold': hhold, 'creg': creg,
                       'extids': gparams, 'health': health,
                       'hhmembers': hhmembers, 'school': school,
                       'care_giver': care_giver, 'services': services,
                       'allow_edit': allow_edit, 'suppression': vl_sup,
                       'criterias': criterias,
                       'well_being_count': wellbeing_services
                       })
    except Exception as e:
        print("error with OVC viewing - %s" % (str(e)))
        # raise e
        msg = "Error during ovc view - Complete initial registration form"
        messages.error(request, msg)
        url = reverse('ovc_register', kwargs={'id': id})
        return HttpResponseRedirect(url)


@login_required(login_url='/')
def hh_manage(request, hhid):
    """Some default page for Server Errors."""
    try:
        check_fields = ['hiv_status_id', 'immunization_status_id',
                        'education_level_id']
        vals = get_dict(field_name=check_fields)
        hhmembers = OVCHHMembers.objects.filter(
            is_void=False, house_hold_id=hhid).order_by("-hh_head")
        for hhm in hhmembers:
            pid = hhm.person_id
            ovc = get_health(pid)
            extra = get_extra_info(pid)
            setattr(hhm, 'health', ovc)
            setattr(hhm, 'extra', extra)
        return render(request, 'ovc/household.html',
                      {'status': 200, 'hhmembers': hhmembers,
                       'vals': vals, 'hhid': hhid})
    except Exception as e:
        print("error getting hh members - %s" % (str(e)))
        raise e


@login_required(login_url='/')
# @validate_ovc([], 1)
# @is_allowed_ous(['RGM', 'RGU', 'DSU', 'STD'])
def hh_edit(request, hhid, id):
    """Some default page for Server Errors."""
    try:
        person_id = int(id)
        initial = {}
        person = RegPerson.objects.get(is_void=False, id=person_id)
        health = get_health(person_id)
        check_fields = ['hiv_status_id', 'immunization_status_id',
                        'sex_id']
        vals = get_dict(field_name=check_fields)
        hhmembers = OVCHHMembers.objects.filter(
            is_void=False, house_hold_id=hhid).order_by("-hh_head")
        # Members
        members = []
        ovc_id = 0
        member_type, hiv_status = 'CGOC', ''
        for mm in hhmembers:
            member_id = mm.person_id
            if member_id == person_id:
                member_type = mm.member_type
                hiv_status = mm.hiv_status
            if mm.member_type == 'TOVC':
                ovc_id = member_id
            members.append(mm.person_id)
        ovc = get_ovcdetails(ovc_id)
        if ovc:
            chv_id = ovc.child_chv_id
            members.append(chv_id)
            if chv_id == person_id:
                member_type = 'CCHV'
        member = True if person_id in members else False
        pobj = PersonObj()
        pobj.member_type = member_type
        # Do the POST here
        if request.method == 'POST':
            # health details
            print('HIV', hiv_status)
            if hiv_status == 'HSTP':
                save_health(request, person_id)
            if member_type in ['CCHV', 'CGPM']:
                save_hh_info(request, person_id)
            msg = "HH Information edited successfully"
            messages.info(request, msg)
            url = reverse('hh_manage', kwargs={'hhid': hhid})
            return HttpResponseRedirect(url)
        # Initial data
        link_date, ccc_no, facility_name = '', '', ''
        facility_id, art_status = '', ''
        if health:
            hiv_status = 'HSTP'
            ccc_no = health.ccc_number
            art_status = health.art_status
            facility_id = health.facility_id
            facility_name = health.facility.facility_name
            l_date = health.date_linked
            link_date = l_date.strftime('%d-%b-%Y') if l_date else ''
        # Initial values
        initial['member_type'] = member_type
        initial['ccc_number'] = ccc_no
        initial['facility_id'] = facility_id
        initial['facility'] = facility_name
        initial['art_status'] = art_status
        initial['hiv_status'] = hiv_status
        initial['link_date'] = link_date
        initial['hiv_status'] = hiv_status
        # Extra initial
        params = {}
        extids = RegPersonsExternalIds.objects.filter(
            person_id=person_id, is_void=False)
        for extid in extids:
            params[extid.identifier_type_id] = extid.identifier
        e_initial = {}
        dob = person.date_of_birth
        date_of_birth = dob.strftime('%d-%b-%Y') if dob else ''
        id_num = params['INTL'] if 'INTL' in params else ''
        ed_lvl = params['IHLE'] if 'IHLE' in params else ''
        e_initial['date_of_birth'] = date_of_birth
        e_initial['mobile_number'] = person.des_phone_number
        e_initial['id_number'] = id_num
        e_initial['education_level'] = ed_lvl
        guids = {'guids': [], 'chids': []}
        form = OVCRegistrationForm(guids=guids, data=initial)
        extra_form = OVCExtraInfoForm(data=e_initial)
        return render(request, 'ovc/edit_household.html',
                      {'status': 200, 'hhmembers': hhmembers,
                       'vals': vals, 'form': form, 'person': person,
                       'member': member, 'health': health,
                       'hhid': hhid, 'pobj': pobj, 'ovc': ovc,
                       'extra_form': extra_form, 'ovc_id': ovc_id})
    except Exception as e:
        print("error getting hh members - %s" % (str(e)))
        raise e


@login_required(login_url='/')
def ovc_manage(request):
    """Some default page for Server Errors."""
    try:
        msg = ovc_management(request)
        results = {'message': 'Successful'}
        return JsonResponse(results, content_type='application/json',
                            safe=False)
    except Exception as e:
        msg = "error updating OVC details - %s" % (str(e))
        results = {'message': msg}
        return JsonResponse(results, content_type='application/json',
                            safe=False)

# Audits and May 2024 additions

def ovc_audit_trails(request, id):
    """Method to list all audit trails."""
    try:
        vals = {}
        user_dict = {}
        ovc_id = int(id)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        reg_audits = RegPersonsAuditTrail.objects.filter(person_id=ovc_id)
        services = OVCCareEvents.objects.filter(person_id=ovc_id, date_of_event__gte='2021-10-01')
        user_ids = services.distinct('created_by').values_list('created_by')
        users = AppUser.objects.filter(id__in=user_ids)
        for user in users:
            user_dict[user.id] = user
        for service in services:
            uid = service.created_by
            sid = service.event_type_id
            user = user_dict[uid] if uid in user_dict else None
            evnt = fms[sid] if sid in fms else "%s service" % sid
            mtdt = {"event_id": str(service.event), "HH": service.house_hold_id }
            setattr(service, 'app_user', user)
            setattr(service, 'event', evnt)
            setattr(service, 'meta_data', mtdt)
        # Mobile App
        app_audits = MetadataManagement.objects.filter(person_id=ovc_id)
        afms = {"CPR": "CPARA", "CPT": "Case Plan", "F1A": "Form 1A", "F1B": "Form 1B"}
        for app in app_audits:
            fid = app.form_id
            form_name = afms[fid] if fid in afms else "Form - %s" % fid
            mtdts = {"device_id": app.device_id, "longitude": app.location_lon,
                     "latitude": app.location_lat, "form_id": app.form_id,
                     "interview_start": app.device_start_timestamp,
                     "interview_end": app.device_end_timestamp,
                     "event_id": app.approve_event_id}
            setattr(app, 'meta_data', mtdts)
            setattr(app, 'form_name', form_name)
        return render(request, 'ovc/audit_trails.html',
                      {'status': 200, 'vals': vals, 'ovc_id': ovc_id,
                       'child': child, 'reg_audits': reg_audits,
                       'serv_audits': services, 'app_audits': app_audits})
    except Exception as e:
        raise e
    else:
        pass


def ovc_viral_load(request, id):
    """Method to list all audit trails."""
    try:
        vals = {}
        days = 0
        validity = 0
        msg = "Test required"
        initial = {}
        ovc_id = int(id)
        guids = {'guids': [], 'chids': []}
        form = OVCRegistrationForm(guids=guids, data=initial)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        vloads = OVCViralload.objects.filter(
            is_void=False, person_id=ovc_id).order_by("-viral_date")
        # CG VL
        cg_vloads = OVCViralload.objects.filter(
            is_void=False, person_id=creg.caretaker_id).order_by("-viral_date")
        if vloads:
            cvload = vloads.first()
            viral_load = cvload.viral_load
            days = dates_difference(cvload.viral_date) * -1
            if not viral_load:
                validity = 1
                msg = "Continue management"
            elif viral_load > 0 and viral_load < 50:
                validity = 1
                msg = "Continue management"
            elif viral_load >= 50 and viral_load < 199:
                validity = 2
                msg = "Continue management, Enroll in DSD"
            elif viral_load > 199 and viral_load < 1000:
                validity = 3
                msg = "Institute EAC, repeat VL after 3 months"
            elif viral_load >= 1000:
                validity = 4
                msg = "Conduct EAC, Repeat VL after 3 months, 2nd Line if 2nd Line VL is >1,000 copies"
            else:
                validity = 0
        vl_days = 180 if child.years < 18 else 365
        vl_tracker = OVCVLTracker.objects.filter(person_id=ovc_id).first()
        return render(request, 'ovc/viral_load.html',
                      {'status': 200, 'vals': vals, 'ovc_id': ovc_id,
                       'vloads': vloads, 'child': child, 'form': form,
                       'creg': creg, 'vl_tracker': vl_tracker, 'msg': msg,
                       'cg_vloads': cg_vloads, 'days': days, 'validity': validity,
                       'vl_days': vl_days})
    except Exception as e:
        raise e
    else:
        pass


def ovc_hiv_status(request, id):
    """Method to list all audit trails."""
    try:
        if request.method == 'POST':
            print('Save changes and audit logs')
            msg = "OVC HIV status updated successfully"
            messages.info(request, msg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        initial = {}
        ovc_id = int(id)
        guids = {'guids': [], 'chids': []}
        vals = get_dict(field_name=['hiv_status_id'])
        form = OVCRegistrationForm(guids=guids, data=initial)
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        statuses = OVCHivStatus.objects.filter(
            is_void=False, person_id=ovc_id).order_by("-date_of_event")
        validity = 0
        if statuses:
            validity = get_days_difference(statuses.first().date_of_event)
        return render(request, 'ovc/hiv_status.html',
                      {'status': 200, 'vals': vals, 'ovc_id': ovc_id,
                       'hiv_statuses': statuses, 'child': child, 'form': form,
                       'creg': creg, 'validity': validity})
    except Exception as e:
        raise e
    else:
        pass


def ovc_exits(request, id):
    """Method to list all audit trails."""
    try:
        delta = 0
        vals = {}
        initial = {}
        ovc_id = int(id)
        guids = {'guids': [], 'chids': []}
        child = RegPerson.objects.get(is_void=False, id=ovc_id)
        creg = OVCRegistration.objects.get(is_void=False, person_id=ovc_id)
        ovc_cg_id = creg.caretaker_id
        # Past CPARA
        cpara = OVCCareBenchmarkScore.objects.filter(
            event__event_type_id='cpr',
            event__person_id=ovc_id).order_by('-date_of_event').first()
        # Benchmark Monitoring / HHRCPA
        m_bm = OVCBenchmarkMonitoring.objects.filter(
            event__event_type_id='obm', form_type='bm',
            caregiver_id=ovc_cg_id).order_by('-event__date_of_event').first()
        m_cpa = OVCBenchmarkMonitoring.objects.filter(
            event__event_type_id='obm', form_type='hhrcpa',
            caregiver_id=ovc_cg_id).order_by('-event__date_of_event').first()
        if request.method == 'POST':
            cc_form = request.POST.get('case_closure', None)
            msg = perform_exit(request)
            messages.info(request, msg)
            url = reverse('ovc_view', kwargs={'id': ovc_id})
            if cc_form == 'AYES' and 'success' in msg:
                url = reverse('new_case_closure', kwargs={'id': ovc_id})
            return HttpResponseRedirect(url)
        # Initial details
        if creg.exit_date:
            delta = get_days_difference(creg.exit_date)
            exit_date = creg.exit_date.strftime('%d-%b-%Y')
            exit_org = get_exit_org(ovc_id, True)
            initial['exit_reason'] = creg.exit_reason
            initial['exit_date'] = exit_date, ou_id = '', ''
            ou_name, ou_id = '', ''
            if exit_org:
                ou_name = exit_org.org_unit_name
                ou_id = exit_org.org_unit_id
            initial['exit_org_name'] = ou_name
            initial['exit_org_id'] = ou_id
        form = OVCRegistrationForm(guids=guids, data=initial)
        reg_audits = RegPersonsAuditTrail.objects.filter(person_id=ovc_id)
        return render(request, 'ovc/exit_and_graduation.html',
                      {'status': 200, 'vals': vals, 'ovc_id': ovc_id,
                       'reg_audits': reg_audits, 'child': child,
                       'form': form, 'delta': delta, 'cpara': cpara,
                       'm_bm': m_bm, 'm_cpa': m_cpa})
    except Exception as e:
        raise e
    else:
        pass


def ovc_timeline(request, id):
    """Method to list all audit trails."""
    try:
        vals = {}
        ovc_id = int(id)
        reg_dates = []
        # Keys
        ovc = OVCRegistration.objects.filter(person_id=ovc_id, is_void=False).first()
        reg_date = ovc.registration_date
        exit_date = ovc.exit_date
        dt = datetime.combine(reg_date, datetime.min.time()).timestamp()
        dts = {"x": dt * 1000, "name": "OVC Enrollment",
               "label": "Enrollment", "description": "Program Enrollment"}
        reg_dates.append(dts)
        services = OVCCareEvents.objects.filter(person_id=ovc_id)
        for service in services:
            ev_date = service.date_of_event
            sid = service.event_type_id
            st = datetime.combine(ev_date, datetime.min.time()).timestamp()
            evnt = fms[sid] if sid in fms else "Service - %s" % sid
            sdt = {"x": st * 1000, "name": evnt,
                   "label": evnt, "description": "service"}
            reg_dates.append(sdt)
        if exit_date:
            et = datetime.combine(exit_date, datetime.min.time()).timestamp()
            edts = {"x": et * 1000, "name": "OVC Exit",
               "label": "Exit/Graduation", "description": "Program Exit"}
            reg_dates.append(edts)
        return render(request, 'ovc/timeline.html',
                      {'status': 200, 'vals': vals, 'ovc_id': ovc_id,
                       'reg_dates': reg_dates, 'ovc': ovc})
    except Exception as e:
        raise e
    else:
        pass