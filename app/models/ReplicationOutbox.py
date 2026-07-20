from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from configs.db import Base


class ReplicationOutbox(Base):
    """
    Model ReplicationOutbox - Đại diện cho bảng hàng đợi Outbox dùng để đồng bộ dữ liệu.
    Mỗi khi có thay đổi dữ liệu học phần ở site Primary, một bản ghi sự kiện sẽ được tạo ra tại đây
    để tiến trình chạy ngầm quét và đồng bộ sang các site con (Replica).
    """
    __tablename__ = "ReplicationOutbox"

    # ID sự kiện: Khóa chính của bảng, tự động tăng và được đánh chỉ mục (index)
    EventId = Column(Integer, primary_key=True, autoincrement=True, index=True)
    
    # Loại đối tượng cần đồng bộ: ví dụ "Course" (Học phần)
    EntityType = Column(String(50), nullable=False)
    
    # Định danh của đối tượng: ví dụ mã học phần "IT01"
    EntityId = Column(String(50), nullable=False, index=True)
    
    # Loại thao tác: "UPSERT" (thêm hoặc cập nhật) hoặc "DELETE" (xóa)
    Operation = Column(String(20), nullable=False)
    
    # Dữ liệu chi tiết của đối tượng được tuần tự hóa (serialize) thành chuỗi JSON thô
    Payload = Column(Text, nullable=False)
    
    # Cơ sở nguồn nơi phát sinh sự thay đổi dữ liệu: ví dụ "HADONG"
    SourceSite = Column(String(20), nullable=False)
    
    # Cơ sở đích cần được đồng bộ dữ liệu sang: ví dụ "NGOCTRUC"
    TargetSite = Column(String(20), nullable=False, index=True)
    
    # Trạng thái đồng bộ hiện tại: "PENDING" (chờ xử lý), "DONE" (hoàn thành), hoặc "FAILED" (thất bại)
    Status = Column(String(20), nullable=False, default="PENDING", index=True)
    
    # Số lần hệ thống đã thử đồng bộ lại khi gặp lỗi kết nối tới site đích
    RetryCount = Column(Integer, nullable=False, default=0)
    
    # Nội dung thông báo lỗi chi tiết ghi nhận từ cơ sở dữ liệu đích nếu đồng bộ thất bại
    LastError = Column(Text, nullable=True)
    
    # Thời điểm tạo sự kiện đồng bộ
    CreatedAt = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Thời điểm cập nhật trạng thái bản ghi gần nhất
    UpdatedAt = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    
    # Thời điểm đồng bộ thành công dữ liệu sang site đích (chỉ có giá trị khi Status là "DONE")
    ProcessedAt = Column(DateTime, nullable=True)
