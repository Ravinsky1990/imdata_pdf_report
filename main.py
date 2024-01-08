from report import Report


if __name__ == '__main__':
    # create instance of Report cls
    report_cls = Report('./PCOAed_1778_104_PCOA_In_05262020.csv')
    report_cls.create_report()

