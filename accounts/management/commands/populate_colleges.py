from django.core.management.base import BaseCommand
from accounts.models import College

class Command(BaseCommand):
    help = 'Populates the database with initial college data'

    def handle(self, *args, **kwargs):
        colleges = [
            # Indira Group
            {"name": "School of information Technology, Indira University", "code": "SIT_IU"},
            {"name": "School of Business, Indira University", "code": "SB_IU"},
            {"name": "School of Commerce and Economics, Indira University", "code": "SCE_IU"},
            {"name": "School of Pharmacy, Indira University", "code": "SP_IU"},
            {"name": "School of Liberal Arts, Indira University", "code": "SLA_IU"},
            {"name": "Indira Institute of Management Pune", "code": "IIMP"},
            {"name": "Indira College of Engineering & Management", "code": "ICEM"},
            {"name": "Indira College of Pharmacy", "code": "ICP"},
            {"name": "Indira College of Commerce & Science", "code": "ICCS"},
            {"name": "Indira School of Aviation", "code": "ISA"},
            {"name": "Indira School of Business Studies (ISBS - PGDM)", "code": "ISBS_PGDM"},
            {"name": "Indira Global School of Business", "code": "IGBS"},
            {"name": "Indira School of Communication", "code": "ISC"},
            
            # Sangamner
            {"name": "Sangamner College, Sangamner", "code": "SCS"},
            {"name": "Amrutvahini College of Engineering", "code": "AVCOE"},
            {"name": "Amrutvahini College of Pharmacy", "code": "AVCOP"},
            {"name": "Amrutvahini Polytechnic", "code": "AVP"},
            {"name": "Amrutvahini Institute of Management and Business Administration", "code": "AIMBA"},
            {"name": "S.M.B.T Dental College & Hospital, Sangamner", "code": "SMBT_DENTAL"},
            {"name": "Shramshakti College of Agriculture, Sangamner", "code": "SCAS"},
            {"name": "Shri Omkarnath Malpani Law College, Sangamner", "code": "SOMLC"},
            {"name": "Matoshri Radha College of Pharmacy, Sangamner", "code": "MRCP"},
            {"name": "Ashvin College of Pharmacy, Sangamner", "code": "ACP"},
            {"name": "Vrindavan College of Agriculture, Sangamner", "code": "VCAS"},
            {"name": "Kai Sau Sunitatati Eknatharao Dhakane Polytechnic, Sangamner", "code": "KSED_POLY"},
            {"name": "Dr Bhanudas Dere Ayurved Medical College, Sangamner", "code": "DBDAMC"},
            {"name": "Trimurti Chitrakala Mahavidyalay, Sangamner", "code": "TCM"},
            {"name": "Sangamner College of Education", "code": "SCE"},

            # Pune & Others
            {"name": "Savitribai Phule Pune University", "code": "SPPU"},
            {"name": "Symbiosis International University, Pune", "code": "SIU"},
            {"name": "Bharati Vidyapeeth University, Pune", "code": "BVU"},
            {"name": "College of Engineering Pune (COEP)", "code": "COEP"},
            {"name": "Symbiosis Institute of Technology", "code": "SIT_SYM"},
            {"name": "MIT World Peace University, Pune", "code": "MIT_WPU"},
            {"name": "Vishwakarma Institute of Technology, Pune", "code": "VIT"},
            {"name": "Pune Institute of Computer Technology (PICT)", "code": "PICT"},
            {"name": "Defence Institute of Advanced Technology (DIAT), Pune", "code": "DIAT"},
            {"name": "Army Institute of Technology (AIT), Pune", "code": "AIT"},
            {"name": "Bharati Vidyapeeth College of Engineering, Pune", "code": "BVCOE"},
            {"name": "DY Patil University, Pune", "code": "DYPU"},
            {"name": "Fergusson College, Pune", "code": "FC"},
            {"name": "ILS Law College, Pune", "code": "ILS"},
            {"name": "AISSMS College of Engineering, Pune", "code": "AISSMS"},
            {"name": "AISSMS College of Hotel Management & Catering Technology", "code": "AISSMS_HM"},
            {"name": "National Institute of Bank Management (NIBM), Pune", "code": "NIBM"},
            {"name": "Symbiosis Institute of Business Management (SIBM), Pune", "code": "SIBM"},
            {"name": "Pune Institute of Business Management (PIBM)", "code": "PIBM"},
            {"name": "National Insurance Academy (NIA), Pune", "code": "NIA"},
            {"name": "FLAME University, Pune", "code": "FLAME"},
            {"name": "Gokhale Institute of Politics and Economics, Pune", "code": "GIPE"},
            {"name": "Film and Television Institute of India (FTII), Pune", "code": "FTII"},
            {"name": "Mahindra United World College of India, Pune", "code": "MUWCI"},
            {"name": "Nowrosjee Wadia College, Pune", "code": "NWC"},
            {"name": "Ness Wadia College of Commerce, Pune", "code": "NWCC"},
            {"name": "MES Garware College of Commerce, Pune", "code": "MES_GCC"},
            {"name": "PES Modern College of Engineering, Pune", "code": "PES_MCOE"},
            {"name": "ABhinav Education Society College of Pharmacy, Pune", "code": "AESCP"},
            {"name": "ALARD Institute of Management Sciences, Pune", "code": "AIMS"},
            {"name": "Anand Medical Foundation’s Nursing Institute, Pune", "code": "AMFNI"},
            {"name": "Army Law College, Pune", "code": "ALC"},
            {"name": "ABMSS PY Rao Chavan Law College, Pune", "code": "ABMSS_LC"},
            {"name": "A K Khan Law College, Pune", "code": "AKKLC"},
        ]

        created_count = 0
        for col_data in colleges:
            college, created = College.objects.update_or_create(
                code=col_data['code'],
                defaults={'name': col_data['name']}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created college: {college.name}'))
            else:
                 self.stdout.write(f'Updated college: {college.name}')

        self.stdout.write(self.style.SUCCESS(f'Successfully populated {created_count} new colleges'))
