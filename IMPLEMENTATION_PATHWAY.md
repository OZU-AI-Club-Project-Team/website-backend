# Backend Implementation Pathway
## Based on OpenAPI Specification (`openapi.yaml`)

### Current Status

#### ✅ **Already Implemented:**
1. **Auth Module** (`/auth/*`)
   - ✅ `/auth/send-code` (POST)
   - ✅ `/auth/signin` (POST)
   - ✅ `/auth/refresh` (POST)
   - ✅ `/auth/reset-key` (POST)

2. **User Module** (`/users/*`)
   - ✅ `/users/{id}` (GET) - Note: OpenAPI uses `/user/{id}`, consider alignment
   - ✅ `/users/{id}/team-member` (GET) - Note: OpenAPI uses `/user/{id}/team-member`

3. **Database Schema**
   - ✅ All Prisma models match OpenAPI schemas
   - ✅ All enums are defined correctly

#### ⚠️ **Partially Implemented:**
1. **Application Module** (`/application/*`)
   - ⚠️ Only `/application/{id}/mark-read` exists
   - ❌ Missing: `/application` (GET list)
   - ❌ Missing: `/application/{id}` (GET detail)

#### ❌ **Not Implemented:**
1. **Project Module** (`/project/*`)
   - ❌ `/project` (GET list with `showcase` query param)
   - ❌ `/project/{id}` (GET detail)

2. **Idea Module** (`/idea/*`)
   - ❌ `/idea` (GET list)
   - ❌ `/idea/{id}` (GET detail)

3. **Presentation Module** (`/presentation/*`)
   - ❌ `/presentation` (GET list with `current` query param)
   - ❌ `/presentation/{id}` (GET detail)

---

## Implementation Pathway

### Phase 1: Complete Application Module (Priority: HIGH)
**Why:** Partially implemented, needed for core functionality

**Tasks:**
1. Create `application_schema.py` with response models matching OpenAPI spec
2. Implement `GET /application` - List all applications with proper filtering
3. Implement `GET /application/{id}` - Get application detail with nested relations
4. Update `application_router.py` to include new endpoints
5. Add proper authorization (admin-only for list, appropriate access for detail)

**Files to Create/Modify:**
- `app/modules/application/application_schema.py` (create)
- `app/modules/application/application_controller.py` (modify)
- `app/modules/application/application_router.py` (modify)

---

### Phase 2: Implement Project Module (Priority: HIGH)
**Why:** Core feature for showcasing projects

**Tasks:**
1. Create `project` module structure:
   - `app/modules/project/__init__.py`
   - `app/modules/project/project_schema.py`
   - `app/modules/project/project_controller.py`
   - `app/modules/project/project_router.py`

2. Implement `GET /project`:
   - Support `showcase` query parameter (boolean, optional)
   - Return list with: id, title, date, own, public, showcase
   - Filter by showcase if parameter provided
   - Determine `own` based on current user (leader or member)

3. Implement `GET /project/{id}`:
   - Return full project detail with nested relations:
     - leader (user object)
     - members (array with roles)
     - ideaId (nullable)
   - Handle 404 if project not found
   - Include proper authorization checks

**Files to Create:**
- `app/modules/project/__init__.py`
- `app/modules/project/project_schema.py`
- `app/modules/project/project_controller.py`
- `app/modules/project/project_router.py`

**Files to Modify:**
- `app/routers/index.py` (add project router)

---

### Phase 3: Implement Idea Module (Priority: MEDIUM)
**Why:** Needed for idea management workflow

**Tasks:**
1. Create `idea` module structure:
   - `app/modules/idea/__init__.py`
   - `app/modules/idea/idea_schema.py`
   - `app/modules/idea/idea_controller.py`
   - `app/modules/idea/idea_router.py`

2. Implement `GET /idea`:
   - Return list with: id, title, status, date, own
   - Determine `own` based on current user being an owner

3. Implement `GET /idea/{id}`:
   - Return full idea detail with nested relations:
     - owners (array)
     - teamMembers (array)
     - presentations (array with id, date, done)
     - applicationId (nullable)
   - Handle 404 if idea not found

**Files to Create:**
- `app/modules/idea/__init__.py`
- `app/modules/idea/idea_schema.py`
- `app/modules/idea/idea_controller.py`
- `app/modules/idea/idea_router.py`

**Files to Modify:**
- `app/routers/index.py` (add idea router)

---

### Phase 4: Implement Presentation Module (Priority: MEDIUM)
**Why:** Completes the idea presentation workflow

**Tasks:**
1. Create `presentation` module structure:
   - `app/modules/presentation/__init__.py`
   - `app/modules/presentation/presentation_schema.py`
   - `app/modules/presentation/presentation_controller.py`
   - `app/modules/presentation/presentation_router.py`

2. Implement `GET /presentation`:
   - Support `current` query parameter (boolean, optional)
   - Return list with: id, title, date, done, own
   - Filter by `current` (not yet done) if parameter provided
   - Determine `own` based on current user being in presenting team

3. Implement `GET /presentation/{id}`:
   - Return full presentation detail with nested relations:
     - idea (id, title)
     - owners (array)
     - feedbacks (array with content, user, date)
   - Handle 404 if presentation not found

**Files to Create:**
- `app/modules/presentation/__init__.py`
- `app/modules/presentation/presentation_schema.py`
- `app/modules/presentation/presentation_controller.py`
- `app/modules/presentation/presentation_router.py`

**Files to Modify:**
- `app/routers/index.py` (add presentation router)

---

### Phase 5: Alignment & Testing (Priority: LOW)
**Why:** Ensure consistency with OpenAPI spec

**Tasks:**
1. **Route Prefix Alignment:**
   - Consider changing `/users/{id}` to `/user/{id}` to match OpenAPI spec
   - OR update OpenAPI spec to match current implementation
   - Document decision

2. **Response Model Validation:**
   - Ensure all response models match OpenAPI schemas exactly
   - Verify all required fields are present
   - Check nullable fields are handled correctly

3. **Error Handling:**
   - Ensure 404 responses match OpenAPI spec format
   - Add proper error messages

4. **Authorization:**
   - Review all endpoints for proper authorization
   - Ensure `own` fields are calculated correctly based on current user

5. **Testing:**
   - Write tests for all new endpoints
   - Test query parameters
   - Test authorization scenarios
   - Test 404 cases

---

## Implementation Order Recommendation

1. **Start with Phase 1** (Application Module) - Quick win, partially done
2. **Then Phase 2** (Project Module) - Core feature
3. **Then Phase 3** (Idea Module) - Related to projects
4. **Then Phase 4** (Presentation Module) - Completes workflow
5. **Finally Phase 5** (Alignment & Testing) - Polish and validation

---

## Key Considerations

### Authorization Patterns
- **Public endpoints:** Some endpoints may be public (e.g., showcase projects)
- **Authenticated endpoints:** Require valid token but may be accessible to all authenticated users
- **Admin-only endpoints:** Use `require_roles("ADMIN")` dependency
- **Owner checks:** Use `require_admin_or_self` or custom logic for `own` fields

### Query Parameters
- `showcase` (boolean, optional) - Filter projects
- `current` (boolean, optional) - Filter presentations

### Response Fields
- `own` fields: Determine if current user owns/is member of resource
- `teamMember` fields: Check if user has TeamMember profile
- Nested relations: Include related data (leader, members, owners, etc.)

### Database Queries
- Use Prisma's `include` for nested relations
- Handle soft deletes (`deletedAt` is not null)
- Use proper filtering based on query parameters
- Optimize queries to avoid N+1 problems

---

## Next Steps

**Immediate Action (First Step):**
Start with **Phase 1: Complete Application Module**

1. Create `application_schema.py` with response models
2. Implement `GET /application` endpoint
3. Implement `GET /application/{id}` endpoint
4. Test the endpoints match OpenAPI spec

This will give you a working pattern to follow for the remaining modules.


