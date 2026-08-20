-- ============================================================
-- 燃冰 · AI商务社交 MVP 数据库Schema
-- PostgreSQL 15+ (需要 pgvector 扩展)
-- 版本：v1.0 · 2026-05-04
-- ============================================================
-- 安装扩展
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. users — 用户表
-- ============================================================
CREATE TABLE users (
    id            BIGSERIAL PRIMARY KEY,
    uuid          UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    phone         VARCHAR(20) UNIQUE,
    wx_openid     VARCHAR(128) UNIQUE,
    wx_unionid    VARCHAR(128) UNIQUE,
    nickname      VARCHAR(64),
    avatar_url    VARCHAR(512),
    status        SMALLINT    NOT NULL DEFAULT 1,  -- 1=正常 2=封禁 9=注销
    is_verified   BOOLEAN     NOT NULL DEFAULT FALSE,
    last_login_at TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_users_phone      ON users(phone) WHERE phone IS NOT NULL;
CREATE INDEX idx_users_wx_openid ON users(wx_openid) WHERE wx_openid IS NOT NULL;
CREATE INDEX idx_users_status     ON users(status);

-- ============================================================
-- 2. profiles — 校友档案表
-- ============================================================
CREATE TABLE profiles (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT       NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    real_name       VARCHAR(64)  NOT NULL,
    gender          SMALLINT,  -- 1=男 2=女 0=未知
    birthday        DATE,
    company         VARCHAR(128),
    position        VARCHAR(128),
    industry        VARCHAR(64),
    city            VARCHAR(64),
    bio             TEXT,
    education_year  VARCHAR(10),  -- 入学年份，如 "2015"
    education_major VARCHAR(128), -- 专业
    education_school VARCHAR(128),-- 学校全称
    cert_level      SMALLINT    NOT NULL DEFAULT 0, -- 0=未认证 1=手机认证 2=校友认证 3=深度认证
    cert_status     SMALLINT    NOT NULL DEFAULT 0, -- 0=未提交 1=审核中 2=通过 3=拒绝
    conn_count      INT         NOT NULL DEFAULT 0, -- connections_count 冗余
    active_score    DECIMAL(6,2) NOT NULL DEFAULT 0, -- 活跃度评分（AI计算）
    last_active_at  TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_profiles_user_id     ON profiles(user_id);
CREATE INDEX idx_profiles_cert_level  ON profiles(cert_level);
CREATE INDEX idx_profiles_industry   ON profiles(industry);
CREATE INDEX idx_profiles_school      ON profiles(education_school);
CREATE INDEX idx_profiles_active      ON profiles(active_score DESC);

-- ============================================================
-- 3. tags — 标签表（L1~L5五层）
-- ============================================================
CREATE TABLE tags (
    id          BIGSERIAL PRIMARY KEY,
    name        VARCHAR(64)  NOT NULL,
    l1_category VARCHAR(32)  NOT NULL, -- L1大类：供给资源/需求帮助/行业经验/投资意向/社交兴趣
    l2_group    VARCHAR(32),            -- L2分组
    l3_item     VARCHAR(64),            -- L3具体标签
    l4_attr     VARCHAR(64),            -- L4属性（可选）
    l5_detail   VARCHAR(64),            -- L5细节（可选）
    tag_type    SMALLINT    NOT NULL DEFAULT 1, -- 1=供给 2=需求 3=通用
    is_recommend BOOLEAN   NOT NULL DEFAULT FALSE, -- AI可推荐
    hot_score   INT         NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_tags_category ON tags(l1_category, l2_group);
CREATE INDEX idx_tags_type     ON tags(tag_type);
CREATE INDEX idx_tags_hot      ON tags(hot_score DESC) WHERE is_recommend = TRUE;

-- ============================================================
-- 4. profile_tags — 用户-标签关联表
-- ============================================================
CREATE TABLE profile_tags (
    id          BIGSERIAL PRIMARY KEY,
    profile_id  BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    tag_id      BIGINT      NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    tag_type    SMALLINT    NOT NULL, -- 1=供给标签 2=需求标签（用户自己标注）
    weight      DECIMAL(3,2) NOT NULL DEFAULT 1.0, -- 权重 0.5~1.0
    is_ai_ext   BOOLEAN     NOT NULL DEFAULT FALSE, -- AI推荐添加
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(profile_id, tag_id)
);
CREATE INDEX idx_profile_tags_profile ON profile_tags(profile_id);
CREATE INDEX idx_profile_tags_tag     ON profile_tags(tag_id);
CREATE INDEX idx_profile_tags_type   ON profile_tags(tag_type);

-- ============================================================
-- 5. supplies — 供需表
-- ============================================================
CREATE TABLE supplies (
    id            BIGSERIAL PRIMARY KEY,
    uuid          UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    profile_id    BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    supply_type   SMALLINT    NOT NULL, -- 1=供给(supply) 2=需求(demand)
    title         VARCHAR(256) NOT NULL,
    content       TEXT,
    tags          BIGINT[],              -- tag_ids 数组
    match_count   INT         NOT NULL DEFAULT 0, -- 被匹配次数
    view_count    INT         NOT NULL DEFAULT 0,
    status        SMALLINT    NOT NULL DEFAULT 1, -- 1=有效 2=已下架 3=已成交
    quality_score DECIMAL(4,2),                       -- AI质量评分
    expires_at    TIMESTAMPTZ,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_supplies_profile   ON supplies(profile_id);
CREATE INDEX idx_supplies_type      ON supplies(supply_type);
CREATE INDEX idx_supplies_status    ON supplies(status);
CREATE INDEX idx_supplies_created   ON supplies(created_at DESC);
CREATE INDEX idx_supplies_tags      ON supplies USING GIN(tags);

-- ============================================================
-- 6. profile_embeddings — 用户向量表（pgvector）
-- ============================================================
CREATE TABLE profile_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    profile_id  BIGINT      NOT NULL UNIQUE REFERENCES profiles(id) ON DELETE CASCADE,
    embedding   VECTOR(1536) NOT NULL,
    model_name  VARCHAR(64) NOT NULL DEFAULT 'text-embedding-3-small',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_profile_emb_profile  ON profile_embeddings(profile_id);
CREATE INDEX idx_profile_emb_cosine   ON profile_embeddings USING ivfflat(embedding vector_cosine_ops);

-- ============================================================
-- 7. supply_embeddings — 供需向量表
-- ============================================================
CREATE TABLE supply_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    supply_id   BIGINT      NOT NULL UNIQUE REFERENCES supplies(id) ON DELETE CASCADE,
    embedding   VECTOR(1536) NOT NULL,
    model_name  VARCHAR(64) NOT NULL DEFAULT 'text-embedding-3-small',
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_supply_emb_supply ON supply_embeddings(supply_id);
CREATE INDEX idx_supply_emb_cosine ON supply_embeddings USING ivfflat(embedding vector_cosine_ops);

-- ============================================================
-- 8. matches — AI匹配记录表
-- ============================================================
CREATE TABLE matches (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    supply_id       BIGINT      NOT NULL REFERENCES supplies(id) ON DELETE CASCADE,
    target_profile_id BIGINT    NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    match_score     DECIMAL(5,4) NOT NULL, -- 0.0000~1.0000
    ai_reason       TEXT,                    -- AI匹配理由
    match_type      SMALLINT  NOT NULL, -- 1=供需匹配 2=人脉推荐 3=活动推荐
    status          SMALLINT  NOT NULL DEFAULT 1, -- 1=待处理 2=已联系 3=已成交 4=已忽略
    push_status     SMALLINT  NOT NULL DEFAULT 0, -- 0=未推送 1=已推送 2=已点击 3=已反馈
    feedback_score  SMALLINT,   -- 用户反馈：1=匹配准确 2=一般 3=不匹配
    feedback_text   TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(supply_id, target_profile_id, match_type)
);
CREATE INDEX idx_matches_supply     ON matches(supply_id);
CREATE INDEX idx_matches_target    ON matches(target_profile_id);
CREATE INDEX idx_matches_status    ON matches(status);
CREATE INDEX idx_matches_score     ON matches(match_score DESC);
CREATE INDEX idx_matches_created   ON matches(created_at DESC);
CREATE INDEX idx_matches_push_status ON matches(push_status) WHERE status = 1;

-- ============================================================
-- 9. connections — 关系链表
-- ============================================================
CREATE TABLE connections (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    user_a_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    user_b_id       BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conn_type       SMALLINT    NOT NULL, -- 1=好友 2=粉丝 3=校友 4=活动认识 5=供需认识
    relation_strength DECIMAL(4,2) NOT NULL DEFAULT 0.5, -- 0.0~1.0
    last_interact_at TIMESTAMPTZ,
    interact_count  INT         NOT NULL DEFAULT 0,
    is_mutual       BOOLEAN     NOT NULL DEFAULT FALSE,
    status          SMALLINT    NOT NULL DEFAULT 1, -- 1=有效 2=已删除
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CHECK(user_a_id < user_b_id),  -- 规范：保证user_a_id < user_b_id
    UNIQUE(user_a_id, user_b_id)
);
CREATE INDEX idx_connections_a     ON connections(user_a_id);
CREATE INDEX idx_connections_b     ON connections(user_b_id);
CREATE INDEX idx_connections_users ON connections(user_a_id, user_b_id, status);
CREATE INDEX idx_connections_strength ON connections(relation_strength DESC);

-- ============================================================
-- 10. followups — AI跟进记录表
-- ============================================================
CREATE TABLE followups (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    from_profile_id BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    to_profile_id   BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    trigger_event   SMALLINT    NOT NULL, -- 1=刚匹配 2=活动结束 3=社群互动 4=自定义
    ai_script       TEXT,                  -- AI生成的话术
    followup_type   SMALLINT    NOT NULL DEFAULT 1, -- 1=AI建议 2=已发送 3=已回复 4=已添加微信
    scheduled_at    TIMESTAMPTZ,
    sent_at         TIMESTAMPTZ,
    replied_at      TIMESTAMPTZ,
    result          SMALLINT,  -- 1=positive 2=neutral 3=negative
    result_text     TEXT,
    status          SMALLINT    NOT NULL DEFAULT 0, -- 0=pending 1=scheduled 2=sent 3=completed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_followups_from     ON followups(from_profile_id);
CREATE INDEX idx_followups_to       ON followups(to_profile_id);
CREATE INDEX idx_followups_status   ON followups(status);
CREATE INDEX idx_followups_schedule ON followups(scheduled_at) WHERE status IN (0,1);

-- ============================================================
-- 11. activities — 社交活动表
-- ============================================================
CREATE TABLE activities (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    title           VARCHAR(256) NOT NULL,
    description     TEXT,
    cover_url       VARCHAR(512),
    activity_type   SMALLINT    NOT NULL, -- 1=沙龙 2=路演 3=培训班 4=社交聚会 5=线上讲座
    organizer_id    BIGINT      NOT NULL REFERENCES profiles(id),
    host_school     VARCHAR(128),
    location        VARCHAR(256),
    latitude        DECIMAL(10,7),
    longitude       DECIMAL(10,7),
    start_time      TIMESTAMPTZ NOT NULL,
    end_time        TIMESTAMPTZ,
    max_attendees   INT,
    current_attendees INT       NOT NULL DEFAULT 0,
    enrollment_mode SMALLINT    NOT NULL DEFAULT 1, -- 1=免费 2=付费 3=审核
    fee             DECIMAL(10,2),
    tags            BIGINT[],
    status          SMALLINT    NOT NULL DEFAULT 1, -- 1=报名中 2=进行中 3=已结束 4=已取消
    ai_match_enabled BOOLEAN   NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_activities_status   ON activities(status);
CREATE INDEX idx_activities_start    ON activities(start_time);
CREATE INDEX idx_activities_school   ON activities(host_school);
CREATE INDEX idx_activities_tags     ON activities USING GIN(tags);

-- ============================================================
-- 12. activity_enrollments — 活动报名表
-- ============================================================
CREATE TABLE activity_enrollments (
    id              BIGSERIAL PRIMARY KEY,
    activity_id     BIGINT      NOT NULL REFERENCES activities(id) ON DELETE CASCADE,
    profile_id      BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    enrollment_status SMALLINT  NOT NULL DEFAULT 1, -- 1=已报名 2=已确认 3=已取消 4=已签到
    ai_recommended  BOOLEAN     NOT NULL DEFAULT FALSE,
    ai_match_score  DECIMAL(5,4),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(activity_id, profile_id)
);
CREATE INDEX idx_enroll_activity ON activity_enrollments(activity_id);
CREATE INDEX idx_enroll_profile  ON activity_enrollments(profile_id);
CREATE INDEX idx_enroll_status   ON activity_enrollments(enrollment_status);

-- ============================================================
-- 13. communities — 校友社群表
-- ============================================================
CREATE TABLE communities (
    id              BIGSERIAL PRIMARY KEY,
    uuid            UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    name            VARCHAR(128) NOT NULL,
    description     TEXT,
    community_type  SMALLINT    NOT NULL, -- 1=行业社群 2=地域社群 3=校友群 4=兴趣社群
    school          VARCHAR(128),
    cover_url       VARCHAR(512),
    member_count    INT         NOT NULL DEFAULT 0,
    owner_id        BIGINT      NOT NULL REFERENCES profiles(id),
    status          SMALLINT    NOT NULL DEFAULT 1, -- 1=公开 2=私密 3=已解散
    qr_code_url     VARCHAR(512),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_communities_type  ON communities(community_type);
CREATE INDEX idx_communities_school ON communities(school);
CREATE INDEX idx_communities_status ON communities(status);

-- ============================================================
-- 14. community_members — 社群成员表
-- ============================================================
CREATE TABLE community_members (
    id              BIGSERIAL PRIMARY KEY,
    community_id    BIGINT      NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    profile_id      BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role            SMALLINT    NOT NULL DEFAULT 1, -- 1=普通成员 2=管理员 3=群主
    status          SMALLINT    NOT NULL DEFAULT 1, -- 1=正常 2=已退出 3=已移除
    joined_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(community_id, profile_id)
);
CREATE INDEX idx_cm_community ON community_members(community_id);
CREATE INDEX idx_cm_profile    ON community_members(profile_id);
CREATE INDEX idx_cm_status    ON community_members(status) WHERE status = 1;

-- ============================================================
-- 15. messages — 社群消息表（简化版，不用微信中间件）
-- ============================================================
CREATE TABLE messages (
    id              BIGSERIAL PRIMARY KEY,
    community_id    BIGINT      NOT NULL REFERENCES communities(id) ON DELETE CASCADE,
    profile_id      BIGINT      NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    content         TEXT,
    msg_type        SMALLINT    NOT NULL DEFAULT 1, -- 1=文本 2=图片 3=链接 4=小程序
    is_pinned       BOOLEAN     NOT NULL DEFAULT FALSE,
    like_count      INT         NOT NULL DEFAULT 0,
    ai_signal_type  SMALLINT,  -- AI识别信号：1=供需 2=问答 3=合作意向 4=资源推介
    ai_signal_extracted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_messages_community ON messages(community_id);
CREATE INDEX idx_messages_ai_signal ON messages(ai_signal_type) WHERE ai_signal_type IS NOT NULL;
CREATE INDEX idx_messages_created   ON messages(created_at DESC);

-- ============================================================
-- 16. ai_conversations — AI对话会话表
-- ============================================================
CREATE TABLE ai_conversations (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT      NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID        NOT NULL DEFAULT uuid_generate_v4() UNIQUE,
    channel         SMALLINT    NOT NULL, -- 1=AI助手(Q) 2=AI发布引导(S) 3=AI匹配反馈(K)
    title           VARCHAR(256),
    context_summary TEXT,  -- AI生成的上下文摘要
    message_count   INT         NOT NULL DEFAULT 0,
    last_message_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_conv_user   ON ai_conversations(user_id);
CREATE INDEX idx_ai_conv_recent ON ai_conversations(user_id, last_message_at DESC);

-- ============================================================
-- 17. ai_messages — AI对话消息表
-- ============================================================
CREATE TABLE ai_messages (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id BIGINT       NOT NULL REFERENCES ai_conversations(id) ON DELETE CASCADE,
    role            SMALLINT    NOT NULL, -- 1=user 2=assistant 3=system
    content         TEXT,
    ai_model        VARCHAR(64),
    tokens_used     INT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX idx_ai_msg_conv ON ai_messages(conversation_id);
CREATE INDEX idx_ai_msg_role ON ai_messages(role);

-- ============================================================
-- 触发器：保持冗余计数一致
-- ============================================================
CREATE OR REPLACE FUNCTION update_conn_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE profiles
    SET conn_count = (
        SELECT COUNT(*) FROM connections
        WHERE (user_a_id = (SELECT user_id FROM profiles WHERE id = NEW.profile_id)
               OR user_b_id = (SELECT user_id FROM profiles WHERE id = NEW.profile_id))
        AND status = 1
    )
    WHERE id = NEW.profile_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- connections表变化时，更新profiles.conn_count
-- 注意：需要为profile_id对应的user_id建立索引

-- ============================================================
-- 触发器：自动更新updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION auto_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at          BEFORE UPDATE ON users          FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_profiles_updated_at       BEFORE UPDATE ON profiles       FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_supplies_updated_at       BEFORE UPDATE ON supplies       FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_matches_updated_at        BEFORE UPDATE ON matches        FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_followups_updated_at      BEFORE UPDATE ON followups      FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_activities_updated_at    BEFORE UPDATE ON activities     FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
CREATE TRIGGER trg_communities_updated_at    BEFORE UPDATE ON communities    FOR EACH ROW EXECUTE FUNCTION auto_updated_at();
