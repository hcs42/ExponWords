# This file is part of ExponWords.
#
# ExponWords is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# ExponWords is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along with
# ExponWords.  If not, see <http://www.gnu.org/licenses/>.

# Copyright (C) 2011 Csaba Hoch

import ew.models
from django.contrib import admin

class WordPairInline(admin.TabularInline):
    model = ew.models.WordPair
    extra = 1

class WordListAdmin(admin.ModelAdmin):
    inlines = [WordPairInline]

admin.site.register(ew.models.WDict, WordListAdmin)
admin.site.register(ew.models.EWUser)
