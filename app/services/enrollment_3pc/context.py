from dataclasses import dataclass

from enums.status import EnrollmentAction


@dataclass
class Enrollment3PCContext:
    txn_id: str
    coordinator_site: str
    action: EnrollmentAction
    user_id: str
    ma_sv: str | None = None  
    site_home: str = ""
    site_new: str = ""
    site_old: str | None = None
    target_ma_lop_hp: str = ""
    target_ma_hp: str = ""
    target_ma_hoc_ky: str = ""
    old_ma_lop_hp: str | None = None
    ghi_chu: str | None = None
    lock_sites: list[str] = None

    @property
    def participant_sites(self) -> list[str]:
        ordered: list[str] = []
        for site in (self.site_old, self.site_new, self.site_home):
            if site and site not in ordered:
                ordered.append(site)
        return ordered

    @property
    def transaction_sites(self) -> list[str]:
        ordered: list[str] = []
        for site in (self.coordinator_site, *self.participant_sites):
            if site and site not in ordered:
                ordered.append(site)
        return ordered

    def payload(self) -> dict:
        return {
            "txn_id": self.txn_id,
            "coordinator_site": self.coordinator_site,
            "action": self.action.value,
            "user_id": self.user_id,
            "ma_sv": self.ma_sv,
            "site_home": self.site_home,
            "site_new": self.site_new,
            "site_old": self.site_old,
            "target_ma_lop_hp": self.target_ma_lop_hp,
            "target_ma_hp": self.target_ma_hp,
            "target_ma_hoc_ky": self.target_ma_hoc_ky,
            "old_ma_lop_hp": self.old_ma_lop_hp,
            "ghi_chu": self.ghi_chu,
            "lock_sites": self.lock_sites,
        }

    @classmethod
    def from_payload(cls, payload: dict) -> "Enrollment3PCContext":
        return cls(
            txn_id=payload["txn_id"],
            coordinator_site=payload["coordinator_site"],
            action=EnrollmentAction(payload["action"]),
            user_id=payload["user_id"],
            ma_sv=payload.get("ma_sv"),
            site_home=payload["site_home"],
            site_new=payload["site_new"],
            site_old=payload.get("site_old"),
            target_ma_lop_hp=payload["target_ma_lop_hp"],
            target_ma_hp=payload["target_ma_hp"],
            target_ma_hoc_ky=payload["target_ma_hoc_ky"],
            old_ma_lop_hp=payload.get("old_ma_lop_hp"),
            ghi_chu=payload.get("ghi_chu"),
            lock_sites=payload.get("lock_sites") or [],
        )
