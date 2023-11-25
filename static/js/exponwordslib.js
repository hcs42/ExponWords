// Copyright (C) 2011- Csaba Hoch
// 
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
// 
//     http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function ew_strip(str) {
    return str.replace(/^\s+/, '').replace(/\s+$/, '');
}

// Returns the current date in yyyy-mm-dd format
function get_now_date() {
    var now = new Date();
    y = now.getFullYear();
    m = now.getMonth() + 1;
    d = now.getDate();
    if (d < 10) { d = '0' + d; }
    if (m < 10) { m = '0' + m; }
    return y + '-' + m + '-' + d;
}
