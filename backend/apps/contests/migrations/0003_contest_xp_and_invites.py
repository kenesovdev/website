import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contests', '0002_scoreboardsnapshot_alter_contestproblem_options_and_more'),
        ('submissions', '0003_failedsubmission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='contest',
            name='participation_type',
            field=models.CharField(
                choices=[('OPEN', 'Open'), ('INVITE_ONLY', 'Invite only')],
                default='OPEN',
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name='contestproblem',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='contestproblem',
            name='xp_reward',
            field=models.PositiveIntegerField(default=50),
        ),
        migrations.AddField(
            model_name='contestregistration',
            name='last_solve_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='contestregistration',
            name='total_xp',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterModelOptions(
            name='contestproblem',
            options={'ordering': ['order', 'order_label']},
        ),
        migrations.CreateModel(
            name='ContestInvite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('PENDING', 'Pending'), ('ACCEPTED', 'Accepted')],
                    default='PENDING',
                    max_length=10,
                )),
                ('invited_at', models.DateTimeField(auto_now_add=True)),
                ('contest', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='invites',
                    to='contests.contest',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='contest_invites',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'unique_together': {('contest', 'user')},
            },
        ),
        migrations.CreateModel(
            name='ContestProblemSolve',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('xp_awarded', models.PositiveIntegerField()),
                ('solved_at', models.DateTimeField(auto_now_add=True)),
                ('contest', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contests.contest')),
                ('problem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='problems.problem')),
                ('submission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='submissions.submission')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'contest', 'problem')},
            },
        ),
    ]
