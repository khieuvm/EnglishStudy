#!/usr/bin/env bash
# Đổi bundle ID + App Group hàng loạt trong toàn bộ project.
#
# Dùng:  ./rename.sh com.tenban vocabspike
#        (tham số 1 = prefix bundle ID của bạn, tham số 2 = tên app, chữ thường)
#
# Chạy trên macOS/Linux. Phải chạy TRƯỚC khi mở Xcode.

set -euo pipefail

if [ $# -ne 2 ]; then
  echo "Dùng: $0 <bundle-prefix> <app-name>"
  echo "Ví dụ: $0 com.tenban vocabspike"
  exit 1
fi

PREFIX="$1"
APPNAME="$2"

OLD_BUNDLE="com.example.vocabspike"
OLD_GROUP="group.com.example.vocabspike"
NEW_BUNDLE="${PREFIX}.${APPNAME}"
NEW_GROUP="group.${PREFIX}.${APPNAME}"

cd "$(dirname "$0")"

# macOS sed cần đối số rỗng sau -i
SED_INPLACE=(-i '')
if [ "$(uname)" != "Darwin" ]; then SED_INPLACE=(-i); fi

# Thay group TRƯỚC (vì nó chứa chuỗi bundle bên trong)
find Sources project.yml -type f \( -name '*.swift' -o -name '*.entitlements' -o -name '*.yml' -o -name '*.plist' \) -print0 \
  | xargs -0 sed "${SED_INPLACE[@]}" "s|${OLD_GROUP}|${NEW_GROUP}|g"

find Sources project.yml -type f \( -name '*.swift' -o -name '*.entitlements' -o -name '*.yml' -o -name '*.plist' \) -print0 \
  | xargs -0 sed "${SED_INPLACE[@]}" "s|${OLD_BUNDLE}|${NEW_BUNDLE}|g"

echo "Xong."
echo "  Bundle ID app    : ${NEW_BUNDLE}"
echo "  Bundle ID widget : ${NEW_BUNDLE}.widget"
echo "  App Group        : ${NEW_GROUP}"
echo
echo "Bước tiếp theo: tạo App Group '${NEW_GROUP}' trong Xcode (tab Signing & Capabilities)."
