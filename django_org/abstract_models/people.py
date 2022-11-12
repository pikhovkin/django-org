from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_org.exceptions import IDMismatchError
from django_org.settings import DJANGO_ORG_ENTERPRISE, DJANGO_ORG_POST, DJANGO_ORG_DEPARTMENT, DJANGO_ORG_PERSON


__all__ = (
    'AbstractPerson',
    'AbstractEmployee',
)


User = get_user_model()


class AbstractPerson(models.Model):
    user = models.OneToOneField(User, related_name='person', null=True, blank=True, on_delete=models.SET_NULL)
    first_name = models.CharField(_('First name'), max_length=64)
    middle_name = models.CharField(_('Middle name'), max_length=64, blank=True, default='')
    last_name = models.CharField(_('Last name'), max_length=64, blank=True, default='')

    short_name = models.CharField(_('Short name'), max_length=70, blank=True, default='', editable=False)
    full_name = models.CharField(_('Full name'), max_length=192, blank=True, default='', editable=False)

    class Meta:
        abstract = True
        verbose_name = _('Person')
        verbose_name_plural = _('People')
        ordering = ('last_name', 'middle_name', 'first_name')

    def __str__(self):
        return self.full_name

    @staticmethod
    def _full_name(last_name, first_name, middle_name):
        return f'{last_name} {first_name} {middle_name}'.strip()

    @staticmethod
    def _short_name(last_name, first_name, middle_name):
        if last_name:
            first_name = f'{first_name[0]}.' if first_name else ''
            middle_name = f'{middle_name[0]}.' if middle_name else ''
            return f'{last_name} {first_name} {middle_name}'.strip()

        return f'{first_name} {middle_name}'.strip()

    def url_for_admin_site(self):
        return f'/admin/{self._meta.app_label}/{self._meta.model_name}/{self.pk}/'

    def save(self, **kwargs):
        self.first_name = self.first_name.strip()
        self.middle_name = self.middle_name.strip()
        self.last_name = self.last_name.strip()
        self.short_name = self._short_name(self.last_name, self.first_name, self.middle_name)
        self.full_name = self._full_name(self.last_name, self.first_name, self.middle_name)
        super().save(**kwargs)


class AbstractEmployee(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'),
                                   on_delete=models.PROTECT, editable=False)
    department = models.ForeignKey(DJANGO_ORG_DEPARTMENT, verbose_name=_('Department'), on_delete=models.PROTECT)
    post = models.ForeignKey(DJANGO_ORG_POST, verbose_name=_('Post'), on_delete=models.PROTECT)
    person = models.OneToOneField(DJANGO_ORG_PERSON, verbose_name=_('Person'), on_delete=models.PROTECT)

    class Meta:
        abstract = True
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        unique_together = ('enterprise', 'department', 'post', 'person')
        ordering = ('enterprise', 'department', 'post', 'person')

    def __str__(self):
        return f'{self.enterprise.name}/{self.person.full_name}'

    def save(self, **kwargs):
        if self.enterprise_id is None:
            if self.post.enterprise_id != self.department.enterprise_id:
                raise IDMismatchError('Mismatch of enterprises identifiers')
            self.enterprise_id = self.post.enterprise_id

        super().save(**kwargs)
