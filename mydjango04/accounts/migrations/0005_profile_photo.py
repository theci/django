# Generated by Django 4.2.7 on 2024-01-17 06:16

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_follower_set_user_friend_set"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="photo",
            field=models.ImageField(blank=True, upload_to="profile/photo"),
        ),
    ]
