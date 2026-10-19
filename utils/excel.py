import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def export_applications_to_excel(applications: List[Dict[str, Any]], output_path: Path) -> Path:
    wb = openpyxl.Workbook()
    
    # Sheet 1: Barcha Asosiy Anketalar
    ws = wb.active
    ws.title = "Anketalar (Asosiy)"

    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    left_align = Alignment(horizontal="left", vertical="center")
    
    headers = [
        "ID", "Status", "Confirmation Code", "Ariza Sanasi",
        "Pasport rasm fayli",
        "Familiya (Last Name)", "Ism (First Name)", "Otasining ismi (Middle)",
        "Jinsi", "Tug'ilgan sana", "Tug'ilgan shahar", "Tug'ilgan davlat",
        "Rasm fayli",
        "Manzil (Ko'cha/Uy)", "Shahar/Tuman", "Viloyat", "Pochta indeksi", "Davlat",
        "Hozirgi yashash davlati", "Telefon raqam", "Email",
        "Ta'lim darajasi", "Oilaviy holati", "Farzandlar soni",
        "Turmush o'rtog'i ma'lumoti", "Farzandlar ma'lumoti"
    ]
    
    ws.append(headers)
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align

    for app in applications:
        spouse_info = "Yo'q"
        if app.get("spouse"):
            sp = app["spouse"]
            spouse_info = (
                f"{sp.get('last_name', '')} {sp.get('first_name', '')} | "
                f"Tug'ilgan: {sp.get('birth_date', '')} | {sp.get('gender', '')} | "
                f"{sp.get('birth_city', '')}, {sp.get('birth_country', '')} | "
                f"Rasm: {sp.get('photo_path', '')}"
            )
            
        children_info = "Yo'q"
        if app.get("children"):
            ch_list = []
            for ch in app["children"]:
                ch_list.append(
                    f"#{ch.get('child_index')}: {ch.get('last_name', '')} {ch.get('first_name', '')} | "
                    f"{ch.get('birth_date', '')} | {ch.get('gender', '')} | "
                    f"{ch.get('birth_city', '')} | Rasm: {ch.get('photo_path', '')}"
                )
            children_info = "\n".join(ch_list)

        row_data = [
            app.get("id"),
            app.get("status", "pending"),
            app.get("confirmation_number") or "Kiritilmagan",
            app.get("created_at"),
            app.get("passport_photo_path") or "",
            app.get("last_name"),
            app.get("first_name"),
            app.get("middle_name") or "",
            app.get("gender"),
            app.get("birth_date"),
            app.get("birth_city"),
            app.get("birth_country"),
            app.get("photo_path") or "",
            app.get("address_line1"),
            app.get("city"),
            app.get("district_state"),
            app.get("postal_code"),
            app.get("country"),
            app.get("live_country"),
            app.get("phone_number"),
            app.get("email"),
            app.get("education_level"),
            app.get("marital_status"),
            app.get("children_count", 0),
            spouse_info,
            children_info
        ]
        ws.append(row_data)

    # Sheet 2: Alohida Oilalar (Turmush o'rtoqlari)
    ws_spouse = wb.create_sheet(title="Turmush o'rtoqlari")
    spouse_headers = [
        "Asosiy Anketa ID", "Familiya", "Ism", "Otasining ismi",
        "Jinsi", "Tug'ilgan sana", "Tug'ilgan shahar", "Tug'ilgan davlat", "Rasm yo'li"
    ]
    ws_spouse.append(spouse_headers)
    for col_num in range(1, len(spouse_headers) + 1):
        cell = ws_spouse.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = PatternFill(start_color="333f48", end_color="333f48", fill_type="solid")
        cell.alignment = center_align

    for app in applications:
        if app.get("spouse"):
            sp = app["spouse"]
            ws_spouse.append([
                app.get("id"),
                sp.get("last_name"),
                sp.get("first_name"),
                sp.get("middle_name") or "",
                sp.get("gender"),
                sp.get("birth_date"),
                sp.get("birth_city"),
                sp.get("birth_country"),
                sp.get("photo_path")
            ])

    # Sheet 3: Alohida Farzandlar
    ws_children = wb.create_sheet(title="Farzandlar")
    child_headers = [
        "Asosiy Anketa ID", "Farzand tartibi", "Familiya", "Ism", "Otasining ismi",
        "Jinsi", "Tug'ilgan sana", "Tug'ilgan shahar", "Tug'ilgan davlat", "Rasm yo'li"
    ]
    ws_children.append(child_headers)
    for col_num in range(1, len(child_headers) + 1):
        cell = ws_children.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = PatternFill(start_color="2e5b32", end_color="2e5b32", fill_type="solid")
        cell.alignment = center_align

    for app in applications:
        for ch in app.get("children", []):
            ws_children.append([
                app.get("id"),
                ch.get("child_index"),
                ch.get("last_name"),
                ch.get("first_name"),
                ch.get("middle_name") or "",
                ch.get("gender"),
                ch.get("birth_date"),
                ch.get("birth_city"),
                ch.get("birth_country"),
                ch.get("photo_path")
            ])

    # Format column widths
    for sheet in [ws, ws_spouse, ws_children]:
        for col in sheet.columns:
            max_len = 0
            col_letter = col[0].column_letter
            for cell in col:
                val_str = str(cell.value or "")
                if "\n" in val_str:
                    lines = val_str.split("\n")
                    max_len = max(max_len, max(len(l) for l in lines))
                else:
                    max_len = max(max_len, len(val_str))
            sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 40)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(output_path)
    return output_path
