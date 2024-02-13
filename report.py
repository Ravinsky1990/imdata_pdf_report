import pandas as pd
import calendar
import time
import os
import pdfkit


class Report:
    def __init__(self, csv_file_path=None, job_id=None) -> None:
        self.csv_file_path = csv_file_path
        self.output_pdf_file_name = ''
        self.df = None
        self.df_for_pdf = None
        self.total = 0
        self.data_percentage: dict = {}
        self.export_data: list = []
        self.html_file_name = ''
        # Use job_id or timestamp in file names (to make them unic)
        if job_id:
            self.html_file_name = f'html_{job_id}.html'
            self.html_file_name_additional = f'{job_id}_additional.html'
            self.concat_html = f'{job_id}_concat.html'
            self.output_pdf_file_name = f'Report_for_job_{job_id}.pdf'
        else:
            # Current GMT time in a tuple format
            current_gmt = time.gmtime()
            # get timestamp
            ts = calendar.timegm(current_gmt)
            self.html_file_name = f'html_{ts}.html'
            self.html_file_name_additional = f'{ts}_additional.html'
            self.concat_html = f'{ts}_concat.html'
            self.output_pdf_file_name = f'Report_for_job_{ts}.pdf'
        # initial static values dicts
        self.data_codes: dict = {
            'P1': 0,
            'P2': 0,
            'P3': 0,
            'N1': 0,
            'N2': 0,
            'N3': 0,
            'PC': 0,
            'PP': 0,
            'PR': 0,
            'CA': 0,
            'LA': 0,
            'SA': 0,
            'SM': 0,
            'D2': 0,
            'MN': 0,
            'SD': 0,
        }
        self.code_descriptions: dict = {
            'P1': 'PCOA Moved Up To 1 Mile',
            'P2': 'PCOA Moved 1 to 5 Miles',
            'P3': 'PCOA Moved 5+ Miles',
            'N1': 'NCOA Moved Up To 1 Mile',
            'N2': 'NCOA Moved 1 to 5 Miles',
            'N3': 'NCOA Moved 5+ Miles',
            'PC': 'Cosmetic Change to Address',
            'PP': 'Input Street Address Converted to a PO Box',
            'PR': 'Input Rural Route Converted to a Street Address',
            'CA': 'Confirmed Name at Address',
            'LA': 'LACSLink Address',
            'SA': 'Standardized Address (Name not Confirmed)',
            'SM': 'DMA Mail Preference Suppression',
            'D2': 'No Delivery Point Validation',
            'MN': 'Moved, Left No Forwarding Address',
            'SD': 'Deceased Suppression',
        }

        self.additional_fields: list = [
            {
                'name': 'PCOA_Add_date_first_Seen',
                'meaning': 'The first date that address for that individual was received'
            },
            {
                'name': 'PCOA_Add_date',
                'meaning': 'The last date that address for that individual was received'
            },
            {
                'name': 'Final_Move_Effective_date',
                'meaning': 'Either the date from NCOA or PCOA Move'
            }
        ]

    def create_report(self):
        print(f'Creating pdf report...')
        self.calc_codes_amounts()
        self.calc_total()
        self.calc_percentage()
        self.create_final_data_structure()
        self.create_df_to_process()
        self.convert_df_html()
        self.create_additional_part_html()
        self.concat_main_html_additional()
        self.convert_html_pdf()
        # self.purge_html_artifacts()

    def purge_html_artifacts(self):
        os.remove(self.html_file_name)
        # os.remove(self.output_pdf_file_name)
        os.remove(self.html_file_name_additional)
        os.remove(self.concat_html)
        print(f'Removed html artifacts')

    def purge_pdf_artifacts(self):
        os.remove(self.output_pdf_file_name)
        print(f'Removed pdf artifacts')   

    @staticmethod
    def percentage(part, whole):
        """  Calculates percentage"""
        return 100 * float(part) / float(whole)

    def calc_codes_amounts(self):
        """  Calculates amount of each code"""
        self.df = pd.read_csv(self.csv_file_path, index_col=False)
        print(f'Input csv len - {len(self.df)}')
        for index, row in self.df.iterrows():
            if row['FINAL_REPORT_ID'] in self.data_codes:
                self.data_codes[row['FINAL_REPORT_ID']] += 1

    def calc_total(self):
        """  Calculates total of all codes amounts"""
        for code in self.data_codes:
            self.total = self.total + self.data_codes[code]

    def calc_percentage(self):
        """  Calculates % of each code amount"""
        list_codes = list(self.data_codes)
        for code in list_codes:
            self.data_percentage[code] = round(self.percentage(self.data_codes[code], len(self.df)), 2)

    def create_final_data_structure(self):
        """ Create final data structure list[dict] for future converting"""
        for code in self.data_codes:
            self.export_data.append({
                'Code': code,
                'Count of FINAL_REPORT_ID': self.data_codes[code],
                '% of input file': self.data_percentage[code],
                'Description': self.code_descriptions[code]
            })

    def create_df_to_process(self):
        """ Create simple dataframe to future transformations"""
        self.df_for_pdf = pd.DataFrame.from_dict(self.export_data)

    def convert_df_html(self):
        """  Convert df with calculated data to html"""
        f = open(f'{self.html_file_name}', 'w')
        a = self.df_for_pdf.to_html(index=False)
        f.write(a)
        f.close()

    def create_additional_part_html(self):
        """  Create second part (named Additional fields)"""
        additional_fields_df = pd.DataFrame.from_dict(self.additional_fields)
        f = open(f'{self.html_file_name_additional}', 'w')
        a = additional_fields_df.to_html(header=False, index=False)
        f.write(a)
        f.close()

    def concat_main_html_additional(self):
        main_html = open(self.html_file_name, 'r')
        additional_html = open(self.html_file_name_additional, 'r')
        content_main_html = main_html.read()
        content_additional_html = additional_html.read()
        main_html.close()
        additional_html.close()
        # Open the destination concatenated file
        concat_html = open(self.concat_html, 'w')
        concat_html.write(content_main_html + content_additional_html)
        # Close the destination file
        concat_html.close()

    def convert_html_pdf(self) -> None:
        """  Convert html file to pdf file"""
        pdfkit.from_file(f'{self.concat_html}',
                         f'{self.output_pdf_file_name}')
        print(f'Report created - file {self.output_pdf_file_name}')
