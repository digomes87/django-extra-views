from django.views.generic.base import TemplateResponseMixin, View
from django.http import HttpResponseRedirect, Http404
from django.forms.formsets import formset_factory
from django.forms.models import modelformset_factory
from django.views.generic.list import MultipleObjectMixin, MultipleObjectTemplateResponseMixin


class FormsetMixin(object):
    initial = {}
    form_class = None
    formset_class = None
    success_url = None
    extra = 2
    max_num = None
    can_order = False
    can_delete = False
    
    def construct_formset(self):
        return self.get_formset()(initial=self.get_initial(), **self.get_formset_kwargs())

    def get_initial(self):
        return self.initial

    def get_formset_class(self):
        return self.formset_class

    def get_form_class(self):
        return self.form_class

    def get_formset(self):
        return formset_factory(self.get_form_class(), **self.get_factory_kwargs())
    
    def get_formset_kwargs(self):
        kwargs = {}
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
                'files': self.request.FILES,
            })
        return kwargs

    def get_factory_kwargs(self):
        kwargs = {
            'extra': self.extra,
            'max_num': self.max_num,
            'can_order': self.can_order,
            'can_delete': self.can_delete,
        }
        
        if self.get_formset_class():
            kwargs['formset'] = self.get_formset_class()
        
        return kwargs

    def get_context_data(self, **kwargs):
        return kwargs

    def get_success_url(self):
        if self.success_url:
            url = self.success_url
        else:
            # Default to returning to the same page
            url = self.request.get_full_path() 
        return url

    def formset_valid(self, formset):
        return HttpResponseRedirect(self.get_success_url())

    def formset_invalid(self, formset):
        return self.render_to_response(self.get_context_data(formset=formset))


class ModelFormsetMixin(FormsetMixin, MultipleObjectMixin):
    exclude = None
    fields = None
    
    def construct_formset(self):
        return self.get_formset()(queryset=self.get_queryset(), **self.get_formset_kwargs())

    def get_factory_kwargs(self):
        kwargs = super(ModelFormsetMixin, self).get_factory_kwargs()
        kwargs.update({
            'exclude': self.exclude,
            'fields': self.fields,
        })
        if self.get_form_class():
            kwargs['form'] = self.get_form_class()
        if self.get_formset_class():
            kwargs['formset'] = self.get_formset_class()
        return kwargs
    
    def get_formset(self):
        return modelformset_factory(self.model, **self.get_factory_kwargs())
    
    def formset_valid(self, formset):
        self.object_list = formset.save()
        return super(ModelFormsetMixin, self).formset_valid(formset)        


class ProcessFormsetView(View):
    """
    A mixin that processes a fomset on POST.
    """
    def get(self, request, *args, **kwargs):
        formset = self.construct_formset()
        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request, *args, **kwargs):
        formset = self.construct_formset()
        if formset.is_valid():
            return self.formset_valid(formset)
        else:
            return self.formset_invalid(formset)

    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class BaseFormsetView(FormsetMixin, ProcessFormsetView):
    """
    A base view for displaying a formset
    """


class FormsetView(TemplateResponseMixin, BaseFormsetView):
    """
    A view for displaying a formset, and rendering a template response
    """


class BaseModelFormsetView(ModelFormsetMixin, ProcessFormsetView):
    """
    A base view for displaying a modelformset
    """
    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super(BaseModelFormsetView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        return super(BaseModelFormsetView, self).post(request, *args, **kwargs)


class ModelFormsetView(MultipleObjectTemplateResponseMixin, BaseModelFormsetView):
    """
    A view for displaying a modelformset, and rendering a template response
    """

