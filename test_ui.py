import streamlit as st
import pandas as pd
import internal_api_helpers as api
import os
from entities import User, UserReference, Fund, FundReference, League
def clear_session_state() -> None:
	keys = ["mode_select","user_id"]
	for key in keys:
		st.session_state.pop(key)


def user_label(ref: UserReference) -> str:
	return ref.display_name

def league_view_page() -> None:
	pass

def fund_view_page() -> None:
	pass

def user_view_page() -> None:
	users = api.loadAllUserRefs()
	user_session_key = "user_id" in st.session_state
	
	if user_session_key and st.button("Clear Loaded User"):
		st.session_state.pop("user_id",None)
		st.session_state.pop("user",None)
		st.rerun()
	if not user_session_key:
		selected_user = st.selectbox("User:", users, index=0, format_func=user_label)
		if st.button("Load User",disabled=user_session_key):
			if not selected_user:
				st.warning("No User Selected")
				return
			output = api.loadFullUserDict(selected_user.id)
			st.session_state["user_id"] = output["id"]
			st.session_state["user"] = output
			st.rerun()
	if not user_session_key:
		return
	output = st.session_state.get("user",None)

	if not output:
		st.warning("No User Found")
		return
	user_id = st.session_state.get("user_id")
	st.write("Loaded User: ")
	st.dataframe(pd.DataFrame([output]))
	
	if st.button("Load User's Funds"):
		funds = api.getUserFunds(user_id)
		st.dataframe(pd.DataFrame(funds))


	




def test_page_home() -> None:
	st.header("Fantasy Markets")
	mode_options = ["League","Fund","User"]
	#mode = st.menu_button("View Mode", mode_options,key="mode_select")
	mode = "User"
	if mode is None:
		return

	if mode == "League":
		league_view_page()
	elif mode == "Fund":
		fund_view_page()
	elif mode == "User":
		user_view_page()



test_page_home()