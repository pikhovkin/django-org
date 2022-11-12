from django.db import models
from django.utils.translation import gettext_lazy as _

from django_org.settings import DJANGO_ORG_ENTERPRISE, DJANGO_ORG_DEPARTMENT_TYPE


__all__ = (
    'AbstractDepartmentType',
    'AbstractDepartment',
)


class AbstractDepartmentType(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'), on_delete=models.PROTECT)
    name = models.CharField(_('Name'), max_length=64)

    class Meta:
        abstract = True
        verbose_name = _('Department type')
        verbose_name_plural = _('Department types')
        unique_together = ('enterprise', 'name')
        ordering = ('enterprise', 'name')

    def __str__(self):
        return f'{self.enterprise.name}/{self.name}'


class AbstractDepartment(models.Model):
    enterprise = models.ForeignKey(DJANGO_ORG_ENTERPRISE, verbose_name=_('Enterprise'),
                                   on_delete=models.PROTECT, editable=False)
    department_type = models.ForeignKey(DJANGO_ORG_DEPARTMENT_TYPE, verbose_name=_('Department type'),
                                        on_delete=models.PROTECT)
    parent = models.ForeignKey('self', verbose_name=_('Parents department'),
                               blank=True, null=True, on_delete=models.PROTECT)
    name = models.CharField(_('Name'), max_length=64)

    class Meta:
        abstract = True
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        unique_together = ('parent', 'department_type', 'name')
        ordering = ('enterprise__name', 'parent__name', 'department_type__name', 'name')

    def __str__(self):
        return f'{self.enterprise.name}/{self.department_type.name}/{self.name}'

    def save(self, **kwargs):
        if self.enterprise_id is None:
            self.enterprise_id = self.department_type.enterprise_id

        super().save(**kwargs)
