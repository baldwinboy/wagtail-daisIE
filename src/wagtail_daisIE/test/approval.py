def approve_source(source):
    from .models import ApprovalTarget

    target, _created = ApprovalTarget.objects.get_or_create(name=source.name)
    return target
