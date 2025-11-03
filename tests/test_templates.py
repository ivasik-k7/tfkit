from tfkit.templates.template_factory import TemplateFactory


def test_templates():
    print("🧪 Testing Template Factory...")

    factory = TemplateFactory()
    print(f"✅ Available templates: {factory.get_available_templates()}")

    for template_type in factory.get_available_templates():
        exists = factory.template_exists(template_type)
        status = "✅" if exists else "❌"
        print(f"{status} {template_type} template exists: {exists}")

    try:
        html = factory.render("classic", title="Test", data={})
        print("✅ Template rendering successful!")
        print(f"Rendered {len(html)} characters")
    except Exception as e:
        print(f"❌ Template rendering failed: {e}")
