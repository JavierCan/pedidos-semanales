from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from src.pedidos_huevo.emailer import (
    build_final_email_payload,
    can_send_email,
    send_email_with_attachment,
)
from src.pedidos_huevo.storage import (
    add_colaborador,
    add_destinatario,
    build_excel_final_from_template,
    clear_lote,
    delete_colaborador,
    delete_destinatario,
    get_auto_cc_colaboradores_from_lote,
    get_cc_emails_for_lote,
    get_colaborador_by_id,
    get_destinatario_by_id,
    get_excel_preview_rows,
    get_resumen_lote,
    load_colaboradores,
    load_config_envio,
    load_destinatarios,
    load_tipos,
    remove_pedido_lote,
    resolve_config_envio,
    save_config_envio,
    update_colaborador,
    update_destinatario,
    upsert_pedido_lote,
)

st.set_page_config(
    page_title="Pedidos de huevo semanal",
    page_icon="🥚",
    layout="wide",
)

MAX_TOTAL_PEDIDOS = 3


def init_session_state() -> None:
    if "pedidos_lote" not in st.session_state:
        st.session_state["pedidos_lote"] = []

    if "current_colaborador_index" not in st.session_state:
        st.session_state["current_colaborador_index"] = 0

    if "generated_excel_path" not in st.session_state:
        st.session_state["generated_excel_path"] = ""

    if "generated_fecha" not in st.session_state:
        st.session_state["generated_fecha"] = date.today()


def get_lote() -> list[dict]:
    return st.session_state["pedidos_lote"]


def set_lote(items: list[dict]) -> None:
    st.session_state["pedidos_lote"] = items


def go_prev(total_items: int) -> None:
    if total_items <= 0:
        st.session_state["current_colaborador_index"] = 0
        return
    current = st.session_state.get("current_colaborador_index", 0)
    st.session_state["current_colaborador_index"] = max(0, current - 1)


def go_next(total_items: int) -> None:
    if total_items <= 0:
        st.session_state["current_colaborador_index"] = 0
        return
    current = st.session_state.get("current_colaborador_index", 0)
    st.session_state["current_colaborador_index"] = min(total_items - 1, current + 1)


def get_existing_pedido_for_colaborador(colaborador_id: int) -> dict | None:
    for item in get_lote():
        if int(item.get("colaborador_id", 0)) == int(colaborador_id):
            return item
    return None


def build_resumen_dataframe() -> pd.DataFrame:
    resumen = get_resumen_lote(get_lote())
    if not resumen:
        return pd.DataFrame(
            columns=[
                "colaborador",
                "area",
                "rejas_30_normal",
                "rejas_30_jumbo",
                "rejas_18_normal",
                "total_pedidos",
            ]
        )
    return pd.DataFrame(resumen)


def save_current_pedido(
    colaborador: dict,
    values_by_key: dict[str, int],
) -> None:
    item = {
        "colaborador_id": int(colaborador["id"]),
        "colaborador": colaborador["nombre"],
        "area": colaborador.get("area", ""),
        "rejas_30_normal": int(values_by_key.get("rejas_30_normal", 0)),
        "rejas_30_jumbo": int(values_by_key.get("rejas_30_jumbo", 0)),
        "rejas_18_normal": int(values_by_key.get("rejas_18_normal", 0)),
    }

    updated = upsert_pedido_lote(get_lote(), item)
    set_lote(updated)
    st.session_state["generated_excel_path"] = ""


def format_person_label(nombre: str, extra: str = "") -> str:
    extra = (extra or "").strip()
    return f"{nombre} ({extra})" if extra else nombre


def render_captura_tab() -> None:
    colaboradores = [c for c in load_colaboradores() if c.get("activo", True)]
    tipos = [t for t in load_tipos() if t.get("activo", True)]

    st.subheader("Captura semanal")

    if not colaboradores:
        st.error("No hay colaboradores activos. Ve a Configuración y agrega al menos uno.")
        return

    total_colaboradores = len(colaboradores)
    current_index = min(
        st.session_state.get("current_colaborador_index", 0),
        total_colaboradores - 1,
    )
    st.session_state["current_colaborador_index"] = current_index

    current_colaborador = colaboradores[current_index]
    existing_pedido = get_existing_pedido_for_colaborador(int(current_colaborador["id"]))

    top_col_1, top_col_2, top_col_3 = st.columns([1, 3, 1])
    with top_col_1:
        if st.button("◀ Anterior", use_container_width=True):
            go_prev(total_colaboradores)
            st.rerun()
    with top_col_2:
        labels = [f"{idx + 1}. {c['nombre']}" for idx, c in enumerate(colaboradores)]
        selected_label = st.selectbox(
            "Colaborador",
            options=labels,
            index=current_index,
        )
        selected_index = labels.index(selected_label)
        if selected_index != current_index:
            st.session_state["current_colaborador_index"] = selected_index
            st.rerun()
    with top_col_3:
        if st.button("Siguiente ▶", use_container_width=True):
            go_next(total_colaboradores)
            st.rerun()

    st.markdown(f"### {current_colaborador['nombre']}")
    area_text = current_colaborador.get("area", "Sin área")
    correo_text = current_colaborador.get("correo", "") or "Sin correo"
    info_col_1, info_col_2 = st.columns(2)
    with info_col_1:
        st.caption(f"Área: {area_text}")
    with info_col_2:
        st.caption(f"Correo para copia automática: {correo_text}")

    default_values = {
        "rejas_30_normal": int(existing_pedido.get("rejas_30_normal", 0)) if existing_pedido else 0,
        "rejas_30_jumbo": int(existing_pedido.get("rejas_30_jumbo", 0)) if existing_pedido else 0,
        "rejas_18_normal": int(existing_pedido.get("rejas_18_normal", 0)) if existing_pedido else 0,
    }

    no_llevara_default = sum(default_values.values()) == 0 and existing_pedido is not None

    with st.form(f"pedido_form_{current_colaborador['id']}"):
        no_llevara = st.checkbox(
            "No llevará esta semana",
            value=no_llevara_default,
        )

        value_cols = st.columns(len(tipos)) if tipos else [st]
        values_by_key: dict[str, int] = {}

        for idx, tipo in enumerate(tipos):
            clave = tipo["clave"]
            with value_cols[idx]:
                values_by_key[clave] = int(
                    st.number_input(
                        tipo["nombre"],
                        min_value=0,
                        max_value=int(tipo.get("maximo_individual", 3)),
                        step=1,
                        value=0 if no_llevara else default_values.get(clave, 0),
                        disabled=no_llevara,
                        key=f"{clave}_{current_colaborador['id']}",
                    )
                )

        if no_llevara:
            for tipo in tipos:
                values_by_key[tipo["clave"]] = 0

        total_pedidos = sum(values_by_key.values())

        metric_col_1, metric_col_2 = st.columns(2)
        with metric_col_1:
            st.metric("Total", total_pedidos)
        with metric_col_2:
            st.metric("Máximo permitido", MAX_TOTAL_PEDIDOS)

        if total_pedidos > MAX_TOTAL_PEDIDOS:
            st.error(f"El total no puede ser mayor a {MAX_TOTAL_PEDIDOS}.")

        btn_col_1, btn_col_2, btn_col_3 = st.columns(3)
        with btn_col_1:
            save_btn = st.form_submit_button("Guardar", use_container_width=True)
        with btn_col_2:
            save_next_btn = st.form_submit_button("Guardar y siguiente", use_container_width=True)
        with btn_col_3:
            clear_btn = st.form_submit_button("Limpiar", use_container_width=True)

        if clear_btn:
            values_by_key = {tipo["clave"]: 0 for tipo in tipos}
            save_current_pedido(current_colaborador, values_by_key)
            st.success("Se limpió el pedido del colaborador actual.")
            st.rerun()

        if save_btn or save_next_btn:
            if total_pedidos > MAX_TOTAL_PEDIDOS:
                st.error(f"Corrige el pedido. El total no puede ser mayor a {MAX_TOTAL_PEDIDOS}.")
                st.stop()

            save_current_pedido(current_colaborador, values_by_key)
            st.success("Pedido guardado correctamente.")

            if save_next_btn:
                go_next(total_colaboradores)

            st.rerun()

    st.divider()
    render_resumen_captura(colaboradores)


def render_resumen_captura(colaboradores: list[dict]) -> None:
    st.subheader("Resumen de captura")

    resumen_df = build_resumen_dataframe()
    if resumen_df.empty:
        st.info("Todavía no hay pedidos capturados.")
    else:
        st.dataframe(resumen_df, use_container_width=True, hide_index=True)

    captured_ids = {int(x["colaborador_id"]) for x in get_lote()}
    faltantes = [c["nombre"] for c in colaboradores if int(c["id"]) not in captured_ids]

    left, right = st.columns(2)
    with left:
        st.markdown("**Capturados**")
        if captured_ids:
            for row in get_lote():
                st.write(f"• {row['colaborador']}")
        else:
            st.write("Sin capturas todavía.")
    with right:
        st.markdown("**Pendientes**")
        if faltantes:
            for nombre in faltantes:
                st.write(f"• {nombre}")
        else:
            st.write("Todos los colaboradores ya tienen captura.")

    action_col_1, action_col_2 = st.columns(2)
    with action_col_1:
        if st.button("Vaciar todas las capturas", use_container_width=True):
            set_lote(clear_lote())
            st.session_state["generated_excel_path"] = ""
            st.success("Se limpiaron todas las capturas.")
            st.rerun()
    with action_col_2:
        if not resumen_df.empty:
            st.download_button(
                "Descargar resumen CSV",
                data=resumen_df.to_csv(index=False).encode("utf-8-sig"),
                file_name="resumen_pedidos_huevo.csv",
                mime="text/csv",
                use_container_width=True,
            )

    st.divider()
    render_generacion_y_envio()


def render_generacion_y_envio() -> None:
    st.subheader("Generación y envío")

    config_resolved = resolve_config_envio()
    principal = config_resolved["destinatario_principal"]
    copias_destinatarios = config_resolved["copias_destinatarios"]
    copias_auto_colaboradores = get_auto_cc_colaboradores_from_lote(get_lote())
    cc_emails = get_cc_emails_for_lote(get_lote())
    asunto_base = config_resolved["asunto_base"]
    mensaje_base = config_resolved["mensaje_base"]

    if principal is None:
        st.warning("No hay destinatario principal configurado. Ve a Configuración y asígnalo.")
        return

    st.info(
        f"Destinatario principal: {principal['nombre']} ({principal.get('correo', '')})"
    )

    with st.expander("Ver copias que saldrán en el correo", expanded=False):
        st.markdown("**Copias fijas desde destinatarios**")
        if copias_destinatarios:
            for item in copias_destinatarios:
                st.write(f"• {item['nombre']} ({item.get('correo', '')})")
        else:
            st.write("Sin copias fijas.")

        st.markdown("**Copias automáticas desde colaboradores con pedido**")
        if copias_auto_colaboradores:
            for item in copias_auto_colaboradores:
                st.write(f"• {item['nombre']} ({item.get('correo', '')})")
        else:
            st.write("No hay copias automáticas en este lote.")

    preview_rows = get_excel_preview_rows(get_lote())
    if preview_rows:
        preview_df = pd.DataFrame(preview_rows)
        st.markdown("**Vista previa del Excel final**")
        st.dataframe(preview_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay pedidos válidos para generar el Excel.")
        return

    fecha_generacion = st.date_input(
        "Fecha del envío",
        value=st.session_state.get("generated_fecha", date.today()),
        format="YYYY-MM-DD",
    )

    subject, body = build_final_email_payload(
        asunto_base=asunto_base,
        mensaje_base=mensaje_base,
        fecha_texto=fecha_generacion.strftime("%Y-%m-%d"),
    )

    with st.expander("Vista previa del correo", expanded=False):
        st.code(subject, language=None)
        st.text(body)

    btn_col_1, btn_col_2 = st.columns(2)

    with btn_col_1:
        if st.button("Generar Excel final", type="primary", use_container_width=True):
            try:
                output_path = build_excel_final_from_template(
                    lote=get_lote(),
                    fecha_generacion=fecha_generacion,
                )
                st.session_state["generated_excel_path"] = str(output_path)
                st.session_state["generated_fecha"] = fecha_generacion
                st.success(f"Excel generado: {Path(output_path).name}")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    generated_excel_path = st.session_state.get("generated_excel_path", "")
    if generated_excel_path:
        generated_file = Path(generated_excel_path)
        if generated_file.exists():
            st.success(f"Archivo listo: {generated_file.name}")
            with generated_file.open("rb") as f:
                st.download_button(
                    "Descargar Excel generado",
                    data=f.read(),
                    file_name=generated_file.name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

    with btn_col_2:
        if st.button(
            "Enviar correo",
            use_container_width=True,
            disabled=not bool(st.session_state.get("generated_excel_path")),
        ):
            if not can_send_email():
                st.error("SMTP no configurado. Revisa tu archivo .env.")
                st.stop()

            generated_path = Path(st.session_state["generated_excel_path"])
            if not generated_path.exists():
                st.error("Primero genera el Excel final.")
                st.stop()

            if not principal.get("correo"):
                st.error("El destinatario principal no tiene correo.")
                st.stop()

            try:
                send_email_with_attachment(
                    to_emails=[principal["correo"]],
                    cc_emails=cc_emails,
                    subject=subject,
                    body=body,
                    attachment_path=generated_path,
                )
                st.success("Correo enviado correctamente.")
            except Exception as exc:
                st.error(f"No se pudo enviar el correo: {exc}")


def render_configuracion_tab() -> None:
    st.subheader("Configuración")

    subtab_1, subtab_2, subtab_3 = st.tabs([
        "Colaboradores",
        "Destinatarios",
        "Envío",
    ])

    with subtab_1:
        render_admin_colaboradores()

    with subtab_2:
        render_admin_destinatarios()

    with subtab_3:
        render_admin_envio()


def render_admin_colaboradores() -> None:
    colaboradores = load_colaboradores()

    st.markdown("### Colaboradores")
    if colaboradores:
        st.dataframe(pd.DataFrame(colaboradores), use_container_width=True, hide_index=True)
    else:
        st.info("No hay colaboradores registrados.")

    with st.form("add_colaborador_form", clear_on_submit=True):
        nombre = st.text_input("Nombre")
        area = st.text_input("Área")
        correo = st.text_input("Correo (opcional, se usará solo para copias automáticas)")
        activo = st.checkbox("Activo", value=True)
        submitted = st.form_submit_button("Agregar colaborador", use_container_width=True)

        if submitted:
            try:
                add_colaborador(nombre=nombre, area=area, correo=correo, activo=activo)
                st.success("Colaborador agregado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if colaboradores:
        selected_id = st.selectbox(
            "Editar colaborador",
            options=[c["id"] for c in colaboradores],
            format_func=lambda x: next(
                (
                    format_person_label(c["nombre"], c.get("correo", ""))
                    for c in colaboradores
                    if int(c["id"]) == int(x)
                ),
                str(x),
            ),
            key="edit_colaborador_select",
        )

        current = get_colaborador_by_id(int(selected_id))
        if current:
            with st.form("edit_colaborador_form"):
                edit_nombre = st.text_input("Nombre", value=current.get("nombre", ""))
                edit_area = st.text_input("Área", value=current.get("area", ""))
                edit_correo = st.text_input(
                    "Correo (opcional, solo para copias automáticas)",
                    value=current.get("correo", ""),
                )
                edit_activo = st.checkbox("Activo", value=bool(current.get("activo", True)))

                col_1, col_2 = st.columns(2)
                with col_1:
                    save_btn = st.form_submit_button("Guardar cambios", use_container_width=True)
                with col_2:
                    delete_btn = st.form_submit_button("Eliminar", use_container_width=True)

                if save_btn:
                    try:
                        update_colaborador(
                            colaborador_id=int(selected_id),
                            nombre=edit_nombre,
                            area=edit_area,
                            correo=edit_correo,
                            activo=edit_activo,
                        )
                        st.success("Colaborador actualizado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                if delete_btn:
                    try:
                        delete_colaborador(int(selected_id))
                        set_lote(remove_pedido_lote(get_lote(), int(selected_id)))
                        st.success("Colaborador eliminado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def render_admin_destinatarios() -> None:
    destinatarios = load_destinatarios()

    st.markdown("### Destinatarios")
    if destinatarios:
        st.dataframe(pd.DataFrame(destinatarios), use_container_width=True, hide_index=True)
    else:
        st.info("No hay destinatarios registrados.")

    with st.form("add_destinatario_form", clear_on_submit=True):
        nombre = st.text_input("Nombre del destinatario")
        correo = st.text_input("Correo")
        activo = st.checkbox("Activo", value=True)
        submitted = st.form_submit_button("Agregar destinatario", use_container_width=True)

        if submitted:
            try:
                add_destinatario(nombre=nombre, correo=correo, activo=activo)
                st.success("Destinatario agregado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if destinatarios:
        selected_id = st.selectbox(
            "Editar destinatario",
            options=[d["id"] for d in destinatarios],
            format_func=lambda x: next(
                (
                    format_person_label(d["nombre"], d.get("correo", ""))
                    for d in destinatarios
                    if int(d["id"]) == int(x)
                ),
                str(x),
            ),
            key="edit_destinatario_select",
        )

        current = get_destinatario_by_id(int(selected_id))
        if current:
            with st.form("edit_destinatario_form"):
                edit_nombre = st.text_input("Nombre", value=current.get("nombre", ""))
                edit_correo = st.text_input("Correo", value=current.get("correo", ""))
                edit_activo = st.checkbox("Activo", value=bool(current.get("activo", True)))

                col_1, col_2 = st.columns(2)
                with col_1:
                    save_btn = st.form_submit_button("Guardar cambios", use_container_width=True)
                with col_2:
                    delete_btn = st.form_submit_button("Eliminar", use_container_width=True)

                if save_btn:
                    try:
                        update_destinatario(
                            destinatario_id=int(selected_id),
                            nombre=edit_nombre,
                            correo=edit_correo,
                            activo=edit_activo,
                        )
                        st.success("Destinatario actualizado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))

                if delete_btn:
                    try:
                        delete_destinatario(int(selected_id))
                        st.success("Destinatario eliminado.")
                        st.rerun()
                    except Exception as exc:
                        st.error(str(exc))


def render_admin_envio() -> None:
    destinatarios = [d for d in load_destinatarios() if d.get("activo", True)]
    config = load_config_envio()

    st.markdown("### Configuración fija de envío")

    if not destinatarios:
        st.warning("Primero agrega destinatarios activos.")
        return

    destinatario_options = [d["id"] for d in destinatarios]

    principal_index = 0
    if config.get("destinatario_principal_id") in destinatario_options:
        principal_index = destinatario_options.index(config["destinatario_principal_id"])

    with st.form("config_envio_form"):
        principal_id = st.selectbox(
            "Destinatario principal",
            options=destinatario_options,
            index=principal_index,
            format_func=lambda x: next(
                (
                    format_person_label(d["nombre"], d.get("correo", ""))
                    for d in destinatarios
                    if int(d["id"]) == int(x)
                ),
                str(x),
            ),
        )

        default_copias_destinatarios = [
            copy_id
            for copy_id in config.get("copias_destinatarios_ids", [])
            if copy_id in destinatario_options and copy_id != principal_id
        ]

        copias_destinatarios_ids = st.multiselect(
            "Copias fijas desde destinatarios",
            options=[x for x in destinatario_options if x != principal_id],
            default=default_copias_destinatarios,
            format_func=lambda x: next(
                (
                    format_person_label(d["nombre"], d.get("correo", ""))
                    for d in destinatarios
                    if int(d["id"]) == int(x)
                ),
                str(x),
            ),
        )

        asunto_base = st.text_input(
            "Asunto base",
            value=config.get("asunto_base", "Pedido semanal de huevo"),
        )

        mensaje_base = st.text_area(
            "Mensaje base",
            value=config.get(
                "mensaje_base",
                "Buen día,\n\nComparto el archivo semanal de pedidos de huevo.\n",
            ),
            height=160,
        )

        submitted = st.form_submit_button("Guardar configuración de envío", use_container_width=True)

        if submitted:
            try:
                save_config_envio(
                    destinatario_principal_id=int(principal_id),
                    copias_destinatarios_ids=[int(x) for x in copias_destinatarios_ids],
                    asunto_base=asunto_base,
                    mensaje_base=mensaje_base,
                )
                st.success("Configuración de envío guardada.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def main() -> None:
    init_session_state()

    st.title("Pedidos de huevo semanal")
    st.caption("Captura rápida, generación automática del template y envío automático del archivo.")

    tab_1, tab_2 = st.tabs(["Captura", "Configuración"])

    with tab_1:
        render_captura_tab()

    with tab_2:
        render_configuracion_tab()


if __name__ == "__main__":
    main()