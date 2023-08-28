from subprocess import  Popen


LIBRE_OFFICE = 'libreoffice'
def convert_to_pdf(docx_in, pdf_folder_out):
    p = Popen([LIBRE_OFFICE,
               '--headless',
               '--convert-to',
               'pdf',
               '--outdir',
               pdf_folder_out,
               docx_in])
    print([docx_in, '--convert-to', 'pdf'])
    p.communicate()
