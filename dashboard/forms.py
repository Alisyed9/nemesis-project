"""Forms used by the operator dashboard."""

from django import forms

from core.models import DetectionRule


class DetectionRuleForm(forms.ModelForm):
    """Create and edit a detection rule without changing the domain model."""

    class Meta:
        model = DetectionRule
        fields = ["name", "description", "pattern", "severity", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "pattern": forms.TextInput(attrs={"class": "form-control"}),
            "severity": forms.Select(attrs={"class": "form-select"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
