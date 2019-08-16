from django.http import HttpResponseRedirect
from django.views.generic import ListView


class BackupCodesView(ListView):
    template_name = "kagi/backup_codes.html"

    def get_queryset(self):
        return self.request.user.backup_codes.all()

    def post(self, request):
        for i in range(10):
            self.request.user.backup_codes.create_backup_code()
        return HttpResponseRedirect(self.request.build_absolute_uri())
