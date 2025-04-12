from django.db import models


class UppercaseCharFieldMixin(models.Model):
    
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for field in self._meta.fields:
            if isinstance(field, models.CharField):
                value = getattr(self, field.name, None)
                if value and isinstance(value, str):
                    setattr(self, field.name, value.upper())
        super().save(*args, **kwargs)