from .contact import ContactSerializer
from .design import DesignSerializer
from .model_3d import Model3DSerializer
from .product import ItemSerializer, CategorySerializer, ProductSerializer
from .hosting import HostingSerializer
from .portfolio_works import PortfolioWorkSerializer
from .proposal import (
    ProposalListSerializer, ProposalDetailSerializer,
    ProposalCreateUpdateSerializer, ProposalSectionDetailSerializer,
    ProposalSectionListSerializer, ProposalSectionUpdateSerializer,
    ProposalRequirementGroupSerializer, ProposalRequirementItemSerializer,
)
from .blog import (
    BlogPostListSerializer, BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer, BlogPostFromJSONSerializer,
    BlogPostAdminListSerializer, BlogPostAdminDetailSerializer,
    BLOG_JSON_TEMPLATE,
)