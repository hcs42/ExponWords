# Copyright (C) 2011- Csaba Hoch
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ew.models
from django.contrib import admin

class WordPairInline(admin.TabularInline):
    model = ew.models.WordPair
    extra = 1

class WordListAdmin(admin.ModelAdmin):
    inlines = [WordPairInline]

admin.site.register(ew.models.WDict, WordListAdmin)
admin.site.register(ew.models.EWUser)
admin.site.register(ew.models.EWLogEntry)
admin.site.register(ew.models.Announcement)
